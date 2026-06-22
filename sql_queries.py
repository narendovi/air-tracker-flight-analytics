# sql_queries.py — All 11 required SQL queries for Air Tracker project

import mysql.connector
from config import DB_CONFIG, DB_NAME


def get_connection():
    config = DB_CONFIG.copy()
    config["database"] = DB_NAME
    return mysql.connector.connect(**config)


def run_query(title, query, params=None):
    """Execute a query and print results."""
    print(f"\n{'='*60}")
    print(f"Query: {title}")
    print('='*60)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        print(f"{'  |  '.join(columns)}")
        print('-' * 60)
        for row in rows:
            print('  |  '.join(str(val) for val in row))
        print(f"\nTotal rows: {len(rows)}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()


# ── Query 1 ──────────────────────────────────────────────────
def query1():
    run_query(
        "Total flights per aircraft model",
        """
        SELECT ac.model, COUNT(f.flight_id) AS total_flights
        FROM flights f
        JOIN aircraft ac ON f.aircraft_registration = ac.registration
        GROUP BY ac.model
        ORDER BY total_flights DESC
        """
    )


# ── Query 2 ──────────────────────────────────────────────────
def query2():
    run_query(
        "Aircraft assigned to more than 5 flights",
        """
        SELECT ac.registration, ac.model, COUNT(f.flight_id) AS flight_count
        FROM flights f
        JOIN aircraft ac ON f.aircraft_registration = ac.registration
        GROUP BY ac.registration, ac.model
        HAVING flight_count > 5
        ORDER BY flight_count DESC
        """
    )


# ── Query 3 ──────────────────────────────────────────────────
def query3():
    run_query(
        "Airports with more than 5 outbound flights",
        """
        SELECT a.name, a.iata_code, COUNT(f.flight_id) AS outbound_flights
        FROM flights f
        JOIN airport a ON f.origin_iata = a.iata_code
        GROUP BY a.iata_code, a.name
        HAVING outbound_flights > 5
        ORDER BY outbound_flights DESC
        """
    )


# ── Query 4 ──────────────────────────────────────────────────
def query4():
    run_query(
        "Top 3 destination airports by arriving flights",
        """
        SELECT a.name, a.city, COUNT(f.flight_id) AS arriving_flights
        FROM flights f
        JOIN airport a ON f.destination_iata = a.iata_code
        GROUP BY a.iata_code, a.name, a.city
        ORDER BY arriving_flights DESC
        LIMIT 3
        """
    )


# ── Query 5 ──────────────────────────────────────────────────
def query5():
    run_query(
        "Flights labeled Domestic or International",
        """
        SELECT 
            f.flight_number,
            f.origin_iata,
            f.destination_iata,
            CASE 
                WHEN a_orig.country = a_dest.country THEN 'Domestic'
                ELSE 'International'
            END AS flight_type
        FROM flights f
        LEFT JOIN airport a_orig ON f.origin_iata    = a_orig.iata_code
        LEFT JOIN airport a_dest ON f.destination_iata = a_dest.iata_code
        ORDER BY flight_type, f.flight_number
        """
    )


# ── Query 6 ──────────────────────────────────────────────────
def query6():
    run_query(
        "5 most recent arrivals at DEL airport",
        """
        SELECT 
            f.flight_number,
            f.aircraft_registration,
            a.name AS departure_airport,
            f.actual_arrival
        FROM flights f
        LEFT JOIN airport a ON f.origin_iata = a.iata_code
        WHERE f.destination_iata = 'DEL'
          AND f.actual_arrival IS NOT NULL
        ORDER BY f.actual_arrival DESC
        LIMIT 5
        """
    )


# ── Query 7 ──────────────────────────────────────────────────
def query7():
    run_query(
        "Airports with no arriving flights",
        """
        SELECT a.name, a.iata_code, a.city, a.country
        FROM airport a
        WHERE a.iata_code NOT IN (
            SELECT DISTINCT destination_iata 
            FROM flights 
            WHERE destination_iata IS NOT NULL
        )
        """
    )


# ── Query 8 ──────────────────────────────────────────────────
def query8():
    run_query(
        "Flight count by airline and status",
        """
        SELECT 
            f.airline_name,
            SUM(CASE WHEN f.status IN ('Arrived', 'Departed') THEN 1 ELSE 0 END) AS on_time,
            SUM(CASE WHEN f.status = 'Delayed'               THEN 1 ELSE 0 END) AS `delayed`,
            SUM(CASE WHEN f.status = 'Canceled'              THEN 1 ELSE 0 END) AS canceled,
            SUM(CASE WHEN f.status = 'Expected'              THEN 1 ELSE 0 END) AS expected,
            COUNT(*)                                                              AS total
        FROM flights f
        WHERE f.airline_name IS NOT NULL AND f.airline_name != ''
        GROUP BY f.airline_name
        ORDER BY total DESC
        LIMIT 20
        """
    )


# ── Query 9 ──────────────────────────────────────────────────
def query9():
    run_query(
        "All cancelled flights with aircraft and airports",
        """
        SELECT 
            f.flight_number,
            f.aircraft_registration,
            COALESCE(a_orig.name, f.origin_iata)      AS origin_airport,
            COALESCE(a_dest.name, f.destination_iata) AS destination_airport,
            f.scheduled_departure
        FROM flights f
        LEFT JOIN airport a_orig ON f.origin_iata      = a_orig.iata_code
        LEFT JOIN airport a_dest ON f.destination_iata = a_dest.iata_code
        WHERE f.status = 'Canceled'
        ORDER BY f.scheduled_departure DESC
        LIMIT 20
        """
    )


# ── Query 10 ─────────────────────────────────────────────────
def query10():
    run_query(
        "City pairs with more than 2 different aircraft models",
        """
        SELECT 
            f.origin_iata,
            f.destination_iata,
            COUNT(DISTINCT 
                COALESCE(ac.model, f.aircraft_registration)
            ) AS aircraft_models
        FROM flights f
        LEFT JOIN aircraft ac ON f.aircraft_registration = ac.registration
        WHERE f.origin_iata IS NOT NULL 
          AND f.destination_iata IS NOT NULL
          AND f.aircraft_registration IS NOT NULL
        GROUP BY f.origin_iata, f.destination_iata
        HAVING aircraft_models > 2
        ORDER BY aircraft_models DESC
        LIMIT 20
        """
    )


# ── Query 11 ─────────────────────────────────────────────────
def query11():
    run_query(
        "Delay percentage per destination airport",
        """
        SELECT 
            a.name AS airport_name,
            a.iata_code,
            COUNT(f.flight_id)                                              AS total_arrivals,
            SUM(CASE WHEN f.status = 'Delayed' THEN 1 ELSE 0 END)          AS delayed_arrivals,
            ROUND(
                SUM(CASE WHEN f.status = 'Delayed' THEN 1 ELSE 0 END) 
                * 100.0 / COUNT(f.flight_id), 2
            )                                                               AS delay_percentage
        FROM flights f
        JOIN airport a ON f.destination_iata = a.iata_code
        GROUP BY a.iata_code, a.name
        HAVING total_arrivals > 0
        ORDER BY delay_percentage DESC
        """
    )


# ── Run all queries ───────────────────────────────────────────
if __name__ == "__main__":
    print("Running all 11 SQL queries...\n")
    query1()
    query2()
    query3()
    query4()
    query5()
    query6()
    query7()
    query8()
    query9()
    query10()
    query11()
    print("\n\nAll queries completed!")