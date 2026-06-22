# ✈️ Air Tracker: Flight Analytics

A comprehensive aviation data analytics application built with Python, MySQL, and Streamlit.
Fetches real-time flight data from the AeroDataBox API and provides interactive dashboards
for exploring airport networks, flight patterns, and delay statistics.

---

## 📌 Project Overview

| Field | Details |
|-------|---------|
| **Domain** | Aviation / Data Analytics |
| **Tech Stack** | Python, MySQL, Streamlit, Plotly |
| **API** | AeroDataBox via RapidAPI |
| **Data** | 15 airports, 33,000+ flights, 50+ aircraft |

### Business Use Cases
- Airport Exploration: Navigate airport details including locations and timezones
- Flight Trend Analysis: Visualize distributions of departures and arrivals by status and airline
- Operational Insights: Analyze flight delays and statuses across selected airports
- Decision Support: Data-driven insights for scheduling and resource allocation

---

## 🗂️ Project Structure
air_tracker/

├── .env                  # API key & DB credentials (not uploaded to GitHub)

├── config.py             # Config loader

├── db_setup.py           # Create MySQL tables

├── fetch_airports.py     # Fetch airport data from API

├── fetch_flights.py      # Fetch flight data from API

├── fetch_aircraft.py     # Fetch aircraft data from API

├── fetch_delays.py       # Fetch delay statistics from API

├── sql_queries.py        # All 11 SQL queries

├── app.py                # Streamlit application

├── requirements.txt      # Python dependencies

└── README.md             # Project documentation

---

## ⚙️ Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/narendovi/air_tracker.git
cd air_tracker
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the project root:
```env
API_KEY=your_rapidapi_key_here
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=air_tracker
```

### 4. Get Your API Key
- Go to [rapidapi.com](https://rapidapi.com)
- Search for **AeroDataBox**
- Subscribe to the free plan and copy your API key

### 5. Set Up the Database
```bash
python db_setup.py
```

### 6. Fetch Data from API
Run these scripts in order:
```bash
python fetch_airports.py
python fetch_flights.py
python fetch_aircraft.py
python fetch_delays.py
```

---

## ▶️ How to Run the App

```bash
streamlit run app.py
```

Open your browser at: **http://localhost:8501**

---

## 📊 Streamlit App Features

| Page | Description |
|------|-------------|
| 🏠 Homepage Dashboard | Summary stats, flight status charts, delay overview |
| 🔍 Search & Filter Flights | Search by flight number, airline, status, origin |
| 🛫 Airport Details | Location map, flight stats, recent arrivals |
| ⏱️ Delay Analysis | Delay % charts, avg delay by airport |
| 🏆 Route Leaderboards | Busiest routes, most delayed airports |
| 📊 SQL Query Results | All 11 project queries with interactive charts |

---

## 🗄️ Database Schema

### Tables
- **airport** — Airport details (IATA/ICAO codes, location, timezone)
- **flights** — Flight schedules, status, airline, origin/destination
- **aircraft** — Aircraft registration, model, manufacturer
- **airport_delays** — Delay statistics per airport

---

## 📝 SQL Queries

All 11 required SQL queries are implemented in `sql_queries.py` and viewable
in the Streamlit app under the **SQL Query Results** page:

1. Total flights per aircraft model
2. Aircraft assigned to more than 5 flights
3. Airports with more than 5 outbound flights
4. Top 3 destination airports by arriving flights
5. Domestic vs International flight classification
6. 5 most recent arrivals at DEL airport
7. Airports with no arriving flights
8. Flight count by airline and status
9. All cancelled flights with aircraft and airports
10. City pairs with more than 2 different aircraft models
11. Delay percentage per destination airport

---

## 🚀 Skills Demonstrated

1. **Data Extraction** — REST API calls and JSON parsing
2. **SQL Database Management** — Schema design and normalization
3. **Data Analysis** — Writing optimized SQL queries
4. **Visualization** — Interactive Streamlit dashboards with Plotly

---

## ⚠️ Notes

- The free RapidAPI tier has rate limits — add delays between API calls
- The AeroDataBox free plan returns current/upcoming flights only
- Re-running fetch scripts is safe — `INSERT IGNORE` prevents duplicates

---

## 👤 Author

**narendovi**
Project: Air Tracker Flight Analytics