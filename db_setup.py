import mysql.connector
from config import DB_CONFIG, DB_NAME


def get_connection(use_db=True):
    """Create and return a MySQL connection."""
    config = DB_CONFIG.copy()
    if use_db:
        config["database"] = DB_NAME
    return mysql.connector.connect(**config)


def create_database():
    """Create the database if it doesn't exist."""
    conn = get_connection(use_db=False)
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    print(f"Database '{DB_NAME}' created/verified.")
    cursor.close()
    conn.close()


def create_tables():
    """Create all required tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Airport table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS airport (
            airport_id INT AUTO_INCREMENT PRIMARY KEY,
            icao_code VARCHAR(10) UNIQUE,
            iata_code VARCHAR(10) UNIQUE,
            name VARCHAR(200),
            city VARCHAR(100),
            country VARCHAR(100),
            continent VARCHAR(50),
            latitude FLOAT,
            longitude FLOAT,
            timezone VARCHAR(100)
        )
    """)

    # Aircraft table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aircraft (
            aircraft_id INT AUTO_INCREMENT PRIMARY KEY,
            registration VARCHAR(20) UNIQUE,
            model VARCHAR(100),
            manufacturer VARCHAR(100),
            icao_type_code VARCHAR(20),
            owner VARCHAR(100)
        )
    """)

    # Flights table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flights (
            flight_id VARCHAR(50) PRIMARY KEY,
            flight_number VARCHAR(20),
            aircraft_registration VARCHAR(20),
            origin_iata VARCHAR(10),
            destination_iata VARCHAR(10),
            scheduled_departure VARCHAR(30),
            actual_departure VARCHAR(30),
            scheduled_arrival VARCHAR(30),
            actual_arrival VARCHAR(30),
            status VARCHAR(30),
            airline_code VARCHAR(20),
            airline_name VARCHAR(100),
            departure_delay INT DEFAULT 0,
            arrival_delay INT DEFAULT 0
        )
    """)

    # Airport delays table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS airport_delays (
            delay_id INT AUTO_INCREMENT PRIMARY KEY,
            airport_iata VARCHAR(10),
            delay_date VARCHAR(20),
            total_flights INT,
            delayed_flights INT,
            avg_delay_min INT,
            median_delay_min INT,
            canceled_flights INT
        )
    """)

    conn.commit()
    print("All tables created successfully.")
    cursor.close()
    conn.close()


if __name__ == "__main__":
    create_database()
    create_tables()