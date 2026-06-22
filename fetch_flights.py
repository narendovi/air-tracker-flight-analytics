import time
import requests
import mysql.connector
from datetime import datetime, timedelta
from config import HEADERS, API_HOST, DB_CONFIG, DB_NAME

AIRPORT_CODES = [
    "DEL", "BOM", "MAA", "BLR", "HYD",
    "CCU", "AMD", "COK", "GOI", "JAI",
    "LHR", "DXB", "SIN", "BKK", "KUL"
]

REQUEST_DELAY = 6
MAX_RETRIES = 3


def get_connection():
    config = DB_CONFIG.copy()
    config["database"] = DB_NAME
    return mysql.connector.connect(**config)


def fetch_flights(iata_code, start_time, end_time):
    """Fetch flights for an airport within a max 12-hour window."""
    flights = []

    for direction in ["arrival", "departure"]:
        url = (f"https://{API_HOST}/flights/airports/iata/{iata_code}/"
               f"{start_time}/{end_time}")
        params = {
            "direction": direction,
            "withLeg": "true",
            "withCancelled": "true"
        }

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, headers=HEADERS, params=params)

                if response.status_code == 429:
                    wait = 10 * (attempt + 1)
                    print(f"  Rate limited on {direction} for {iata_code}. Waiting {wait}s...")
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                data = response.json()

                # API returns either 'arrivals' or 'departures' key
                items = data.get("arrivals", data.get("departures", []))
                flights.extend(items)
                print(f"  {direction} ({start_time}): {len(items)} flights found")
                break

            except requests.exceptions.RequestException as e:
                print(f"  Error {direction} {iata_code}: {e}")
                break

        time.sleep(REQUEST_DELAY)

    return flights


def parse_and_insert_flight(flight, airport_iata, direction, conn):
    """Parse a single flight and insert into DB."""
    cursor = conn.cursor()

    try:
        # Flight number is the unique identifier from this API
        flight_number = flight.get("number", "").strip()
        if not flight_number:
            return  # skip flights with no number

        departure = flight.get("departure") or {}
        arrival = flight.get("arrival") or {}

        dep_airport = departure.get("airport") or {}
        arr_airport = arrival.get("airport") or {}

        # For arrivals: origin = departure airport, destination = queried airport
        # For departures: origin = queried airport, destination = arrival airport
        if direction == "arrival":
            origin_iata = dep_airport.get("iata", dep_airport.get("name", "Unknown"))
            destination_iata = airport_iata
        else:
            origin_iata = airport_iata
            destination_iata = arr_airport.get("iata", arr_airport.get("name", "Unknown"))

        sched_dep = (departure.get("scheduledTime") or {}).get("local", None)
        actual_dep = (departure.get("revisedTime") or {}).get("local", None)
        sched_arr = (arrival.get("scheduledTime") or {}).get("local", None)
        actual_arr = (arrival.get("revisedTime") or {}).get("local", None)

        status = flight.get("status", "Unknown")

        aircraft = flight.get("aircraft") or {}
        registration = aircraft.get("reg", None)
        aircraft_model = aircraft.get("model", None)

        airline = flight.get("airline") or {}
        airline_code = airline.get("iata", "")
        airline_name = airline.get("name", "")

        # Use flight_number + scheduled_departure as unique ID
        # since the API has no uniqueId field
        flight_id = f"{flight_number}_{sched_dep or sched_arr or 'unknown'}"
        flight_id = flight_id.replace(" ", "_")[:50]

        cursor.execute("""
            INSERT IGNORE INTO flights
            (flight_id, flight_number, aircraft_registration, origin_iata,
             destination_iata, scheduled_departure, actual_departure,
             scheduled_arrival, actual_arrival, status, airline_code, airline_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            flight_id, flight_number, registration,
            origin_iata, destination_iata,
            sched_dep, actual_dep, sched_arr, actual_arr,
            status, airline_code, airline_name
        ))
        conn.commit()

    except Exception as e:
        print(f"  DB insert error: {e} | flight: {flight.get('number')}")
    finally:
        cursor.close()


def fetch_and_store_all_flights():
    """Fetch today's and tomorrow's flights for all airports."""
    conn = get_connection()
    today = datetime.now()

    # Use today + tomorrow (free tier returns current/upcoming flights)
    days = [today, today + timedelta(days=1)]

    for day in days:
        date_str = day.strftime("%Y-%m-%d")

        # Split into two 12-hour windows
        windows = [
            (f"{date_str}T00:00", f"{date_str}T11:59"),
            (f"{date_str}T12:00", f"{date_str}T23:59"),
        ]

        for start_time, end_time in windows:
            print(f"\nWindow: {start_time} → {end_time}")

            for code in AIRPORT_CODES:
                print(f"\n  Airport: {code}")

                for direction in ["arrival", "departure"]:
                    url = (f"https://{API_HOST}/flights/airports/iata/{code}/"
                           f"{start_time}/{end_time}")
                    params = {
                        "direction": direction,
                        "withLeg": "true",
                        "withCancelled": "true"
                    }

                    for attempt in range(MAX_RETRIES):
                        try:
                            response = requests.get(url, headers=HEADERS, params=params)

                            if response.status_code == 429:
                                wait = 10 * (attempt + 1)
                                print(f"    Rate limited. Waiting {wait}s...")
                                time.sleep(wait)
                                continue

                            response.raise_for_status()
                            data = response.json()
                            items = data.get("arrivals", data.get("departures", []))
                            print(f"    {direction}: {len(items)} flights")

                            for flight in items:
                                parse_and_insert_flight(flight, code, direction, conn)
                            break

                        except requests.exceptions.RequestException as e:
                            print(f"    Error {direction} {code}: {e}")
                            break

                    time.sleep(REQUEST_DELAY)

    conn.close()
    print("\nAll flights fetched and stored!")


if __name__ == "__main__":
    fetch_and_store_all_flights()