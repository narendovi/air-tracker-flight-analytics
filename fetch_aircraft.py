import time
import requests
import mysql.connector
from config import HEADERS, API_HOST, DB_CONFIG, DB_NAME

REQUEST_DELAY = 3
MAX_RETRIES = 3


def get_connection():
    config = DB_CONFIG.copy()
    config["database"] = DB_NAME
    return mysql.connector.connect(**config)


def get_unique_registrations(limit=50):
    """Get unique aircraft registrations from flights — limited to avoid API quota."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT aircraft_registration 
        FROM flights 
        WHERE aircraft_registration IS NOT NULL
        AND aircraft_registration != ''
        LIMIT %s
    """, (limit,))
    regs = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    print(f"Found {len(regs)} unique registrations to fetch.")
    return regs


def fetch_aircraft_data(registration):
    """Fetch aircraft details with retry on 429."""
    url = f"https://{API_HOST}/aircrafts/reg/{registration}"

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=HEADERS)

            if response.status_code == 429:
                wait = 10 * (attempt + 1)
                print(f"  Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue

            if response.status_code == 404:
                print(f"  Not found: {registration}")
                return None

            response.raise_for_status()

            # Guard against empty response body
            if not response.text.strip():
                print(f"  Empty response for: {registration}")
                return None

            return response.json()

        except Exception as e:
            print(f"  Error fetching {registration}: {e}")
            return None

    print(f"  Failed after {MAX_RETRIES} retries: {registration}")
    return None


def insert_aircraft(data):
    """Insert aircraft data into MySQL."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT IGNORE INTO aircraft
            (registration, model, manufacturer, icao_type_code, owner)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data.get("reg"),
            data.get("model"),
            data.get("typeName") or data.get("manufacturer"),
            data.get("icaoType"),
            data.get("operator")
        ))
        conn.commit()
        print(f"  Inserted: {data.get('reg')} - {data.get('model')}")
    except Exception as e:
        print(f"  DB error: {e}")
    finally:
        cursor.close()
        conn.close()


def fetch_and_store_all_aircraft():
    registrations = get_unique_registrations(limit=50)

    for i, reg in enumerate(registrations, 1):
        print(f"[{i}/{len(registrations)}] Fetching: {reg}")
        data = fetch_aircraft_data(reg)
        if data:
            insert_aircraft(data)
        time.sleep(REQUEST_DELAY)

    print("\nAircraft data fetch complete!")


if __name__ == "__main__":
    fetch_and_store_all_aircraft()