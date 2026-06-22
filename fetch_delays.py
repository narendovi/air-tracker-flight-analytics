import requests
import mysql.connector
from datetime import datetime, timedelta
from config import HEADERS, API_HOST, DB_CONFIG, DB_NAME

AIRPORT_CODES = [
    "DEL", "BOM", "MAA", "BLR", "HYD",
    "CCU", "AMD", "COK", "GOI", "JAI",
    "LHR", "DXB", "SIN", "BKK", "KUL"
]


def get_connection():
    config = DB_CONFIG.copy()
    config["database"] = DB_NAME
    return mysql.connector.connect(**config)


def fetch_delay_data(iata_code):
    """Fetch delay statistics for an airport."""
    url = f"https://{API_HOST}/airports/iata/{iata_code}/stats/delays"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching delays for {iata_code}: {e}")
        return None


def insert_delay(iata_code, data):
    """Insert delay data into MySQL."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT INTO airport_delays
            (airport_iata, delay_date, total_flights, delayed_flights,
             avg_delay_min, median_delay_min, canceled_flights)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            iata_code,
            today,
            data.get("totalFlights", 0),
            data.get("delayedFlights", 0),
            data.get("avgDelay", 0),
            data.get("medianDelay", 0),
            data.get("cancelledFlights", 0)
        ))
        conn.commit()
        print(f"  Inserted delays for: {iata_code}")
    except Exception as e:
        print(f"  DB error: {e}")
    finally:
        cursor.close()
        conn.close()


def fetch_and_store_all_delays():
    """Fetch and store delay stats for all airports."""
    print("Fetching airport delay statistics...\n")
    for code in AIRPORT_CODES:
        print(f"Airport: {code}")
        data = fetch_delay_data(code)
        if data:
            insert_delay(code, data)
    print("\nAll delay data fetched and stored!")


if __name__ == "__main__":
    fetch_and_store_all_delays()