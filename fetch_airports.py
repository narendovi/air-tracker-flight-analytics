import requests
import mysql.connector
from config import HEADERS, API_HOST, DB_CONFIG, DB_NAME

# Choose 10-15 airports of your choice
AIRPORT_CODES = [
    "DEL", "BOM", "MAA", "BLR", "HYD",
    "CCU", "AMD", "COK", "GOI", "JAI",
    "LHR", "DXB", "SIN", "BKK", "KUL"
]


def get_connection():
    """Create and return a MySQL connection."""
    config = DB_CONFIG.copy()
    config["database"] = DB_NAME
    return mysql.connector.connect(**config)


def fetch_airport_data(iata_code):
    """Fetch airport info from AeroDataBox API."""
    url = f"https://{API_HOST}/airports/iata/{iata_code}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching airport {iata_code}: {e}")
        return None


def insert_airport(data):
    """Insert airport data into MySQL."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT IGNORE INTO airport 
            (icao_code, iata_code, name, city, country, continent, latitude, longitude, timezone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get("icao"),
            data.get("iata"),
            data.get("fullName"),
            data.get("municipalityName"),
            data.get("country", {}).get("name"),
            data.get("continent", {}).get("name"),
            data.get("location", {}).get("lat"),
            data.get("location", {}).get("lon"),
            data.get("timeZone")
        ))
        conn.commit()
        print(f"Inserted airport: {data.get('iata')} - {data.get('fullName')}")

    except Exception as e:
        print(f"DB Error for {data.get('iata')}: {e}")

    finally:
        cursor.close()
        conn.close()


def fetch_and_store_all_airports():
    """Fetch and store all airports in the list."""
    print("Starting airport data collection...\n")
    for code in AIRPORT_CODES:
        print(f"Fetching: {code}")
        data = fetch_airport_data(code)
        if data:
            insert_airport(data)
    print("\nAll airports fetched and stored!")


if __name__ == "__main__":
    fetch_and_store_all_airports()