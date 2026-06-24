import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
from config import DB_CONFIG, DB_NAME

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Air Tracker: Flight Analytics",
    page_icon="✈️",
    layout="wide"
)

# ── DB connection ─────────────────────────────────────────────
@st.cache_resource
def get_connection():
    config = DB_CONFIG.copy()
    config["database"] = DB_NAME
    return mysql.connector.connect(**config)

def run_query(query, params=None):
    try:
        conn = get_connection()
        df = pd.read_sql(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()

# ── Sidebar navigation ────────────────────────────────────────
st.sidebar.markdown("# ✈️")
st.sidebar.title("✈️ Air Tracker")
page = st.sidebar.radio("Navigation", [
    "🏠 Homepage Dashboard",
    "🔍 Search & Filter Flights",
    "🛫 Airport Details",
    "⏱️ Delay Analysis",
    "🏆 Route Leaderboards",
    "📊 SQL Query Results"
])

# ══════════════════════════════════════════════════════════════
# PAGE 1 — Homepage Dashboard
# ══════════════════════════════════════════════════════════════
if page == "🏠 Homepage Dashboard":
    st.title("✈️ Air Tracker: Flight Analytics Dashboard")
    st.markdown("Real-time aviation insights powered by AeroDataBox API")
    st.divider()

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    total_airports = run_query("SELECT COUNT(*) AS cnt FROM airport").iloc[0]["cnt"]
    total_flights  = run_query("SELECT COUNT(*) AS cnt FROM flights").iloc[0]["cnt"]
    total_aircraft = run_query("SELECT COUNT(*) AS cnt FROM aircraft").iloc[0]["cnt"]
    avg_delay      = run_query("SELECT ROUND(AVG(avg_delay_min),1) AS avg FROM airport_delays").iloc[0]["avg"]

    col1.metric("🛬 Total Airports",  total_airports)
    col2.metric("✈️ Total Flights",   f"{total_flights:,}")
    col3.metric("🛩️ Aircraft",        total_aircraft)
    col4.metric("⏱️ Avg Delay (min)", avg_delay)

    st.divider()

    # Flight status distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Flight Status Distribution")
        df_status = run_query("""
            SELECT status, COUNT(*) AS count
            FROM flights
            GROUP BY status
            ORDER BY count DESC
        """)
        if not df_status.empty:
            fig = px.pie(df_status, names="status", values="count",
                         color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, width="stretch")

    with col2:
        st.subheader("Top 10 Airlines by Flights")
        df_airlines = run_query("""
            SELECT airline_name, COUNT(*) AS total_flights
            FROM flights
            WHERE airline_name IS NOT NULL AND airline_name != ''
            GROUP BY airline_name
            ORDER BY total_flights DESC
            LIMIT 10
        """)
        if not df_airlines.empty:
            fig = px.bar(df_airlines, x="total_flights", y="airline_name",
                         orientation="h", color="total_flights",
                         color_continuous_scale="Blues")
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, width="stretch")

    # Delay heatmap
    st.subheader("Airport Delay Overview")
    df_delays = run_query("""
        SELECT airport_iata, avg_delay_min, delayed_flights,
               total_flights, canceled_flights
        FROM airport_delays
        ORDER BY avg_delay_min DESC
    """)
    if not df_delays.empty:
        fig = px.bar(df_delays, x="airport_iata", y="avg_delay_min",
                     color="delayed_flights", text="avg_delay_min",
                     labels={"avg_delay_min": "Avg Delay (min)",
                             "airport_iata": "Airport"},
                     color_continuous_scale="Reds")
        st.plotly_chart(fig, width="stretch")

# ══════════════════════════════════════════════════════════════
# PAGE 2 — Search & Filter Flights
# ══════════════════════════════════════════════════════════════
elif page == "🔍 Search & Filter Flights":
    st.title("🔍 Search & Filter Flights")
    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        search_term = st.text_input("Search by flight number or airline", "")
    with col2:
        statuses = ["All"] + run_query(
            "SELECT DISTINCT status FROM flights ORDER BY status"
        )["status"].tolist()
        selected_status = st.selectbox("Filter by Status", statuses)
    with col3:
        airports = ["All"] + run_query(
            "SELECT DISTINCT iata_code FROM airport ORDER BY iata_code"
        )["iata_code"].tolist()
        selected_origin = st.selectbox("Filter by Origin Airport", airports)

    # Build dynamic query
    conditions = []
    params = []

    if search_term:
        conditions.append("(f.flight_number LIKE %s OR f.airline_name LIKE %s)")
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    if selected_status != "All":
        conditions.append("f.status = %s")
        params.append(selected_status)
    if selected_origin != "All":
        conditions.append("f.origin_iata = %s")
        params.append(selected_origin)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    df_flights = run_query(f"""
        SELECT f.flight_number, f.origin_iata, f.destination_iata,
               f.status, f.airline_name, f.scheduled_departure,
               f.actual_arrival, f.aircraft_registration
        FROM flights f
        {where}
        ORDER BY f.scheduled_departure DESC
        LIMIT 200
    """, params if params else None)

    st.markdown(f"**{len(df_flights)} flights found**")
    st.dataframe(df_flights, width="stretch", height=500)

# ══════════════════════════════════════════════════════════════
# PAGE 3 — Airport Details
# ══════════════════════════════════════════════════════════════
elif page == "🛫 Airport Details":
    st.title("🛫 Airport Details Viewer")
    st.divider()

    airports_df = run_query("SELECT iata_code, name FROM airport ORDER BY name")
    airport_options = {
        f"{row['iata_code']} — {row['name']}": row["iata_code"]
        for _, row in airports_df.iterrows()
    }

    selected = st.selectbox("Select Airport", list(airport_options.keys()))
    iata = airport_options[selected]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Airport Info")
        df_info = run_query("SELECT * FROM airport WHERE iata_code = %s", (iata,))
        if not df_info.empty:
            row = df_info.iloc[0]
            st.markdown(f"**Name:** {row['name']}")
            st.markdown(f"**City:** {row['city']}")
            st.markdown(f"**Country:** {row['country']}")
            st.markdown(f"**Continent:** {row['continent']}")
            st.markdown(f"**Timezone:** {row['timezone']}")
            st.markdown(f"**Coordinates:** {row['latitude']}, {row['longitude']}")

            # Map
            if pd.notna(row["latitude"]) and pd.notna(row["longitude"]):
                st.map(pd.DataFrame({
                    "lat": [row["latitude"]],
                    "lon": [row["longitude"]]
                }))

    with col2:
        st.subheader("Flight Stats")
        df_stats = run_query("""
            SELECT
                COUNT(*) AS total_flights,
                SUM(CASE WHEN origin_iata = %s THEN 1 ELSE 0 END) AS departures,
                SUM(CASE WHEN destination_iata = %s THEN 1 ELSE 0 END) AS arrivals,
                SUM(CASE WHEN status = 'Delayed' THEN 1 ELSE 0 END) AS 'delayed',
                SUM(CASE WHEN status = 'Canceled' THEN 1 ELSE 0 END) AS canceled
            FROM flights
            WHERE origin_iata = %s OR destination_iata = %s
        """, (iata, iata, iata, iata))

        if not df_stats.empty:
            r = df_stats.iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Flights", int(r["total_flights"]))
            c2.metric("Departures",    int(r["departures"]))
            c3.metric("Arrivals",      int(r["arrivals"]))
            c1.metric("Delayed",  int(r["delayed"]))
            c2.metric("Canceled", int(r["canceled"]))

        st.subheader("Recent Arrivals")
        df_arr = run_query("""
            SELECT flight_number, origin_iata, airline_name, status,
           COALESCE(actual_arrival, scheduled_arrival) AS arrival_time
            FROM flights
            WHERE destination_iata = %s
            ORDER BY arrival_time DESC
             LIMIT 10
            """, (iata,))
        st.dataframe(df_arr, width="stretch")

# ══════════════════════════════════════════════════════════════
# PAGE 4 — Delay Analysis
# ══════════════════════════════════════════════════════════════
elif page == "⏱️ Delay Analysis":
    st.title("⏱️ Delay Analysis")
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Average Delay by Airport")
        df_avg = run_query("""
            SELECT airport_iata, avg_delay_min, median_delay_min
            FROM airport_delays
            ORDER BY avg_delay_min DESC
        """)
        fig = px.bar(df_avg, x="airport_iata", y="avg_delay_min",
                     color="median_delay_min",
                     labels={"avg_delay_min": "Avg Delay (min)",
                             "airport_iata": "Airport"},
                     color_continuous_scale="Oranges")
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.subheader("Delayed vs Canceled Flights")
        df_dc = run_query("""
            SELECT airport_iata, delayed_flights, canceled_flights
            FROM airport_delays
            ORDER BY delayed_flights DESC
        """)
        fig = px.bar(df_dc, x="airport_iata",
                     y=["delayed_flights", "canceled_flights"],
                     barmode="group",
                     labels={"value": "Flights", "airport_iata": "Airport"})
        st.plotly_chart(fig, width="stretch")

    st.subheader("Delay % per Destination Airport")
    df_pct = run_query("""
        SELECT a.name AS airport_name, a.iata_code,
               COUNT(f.flight_id) AS total_arrivals,
               SUM(CASE WHEN f.status = 'Delayed' THEN 1 ELSE 0 END) AS 'delayed',
               ROUND(SUM(CASE WHEN f.status='Delayed' THEN 1 ELSE 0 END)
                     * 100.0 / COUNT(f.flight_id), 2) AS delay_pct
        FROM flights f
        JOIN airport a ON f.destination_iata = a.iata_code
        GROUP BY a.iata_code, a.name
        HAVING total_arrivals > 0
        ORDER BY delay_pct DESC
    """)
    fig = px.bar(df_pct, x="iata_code", y="delay_pct",
                 text="delay_pct", color="delay_pct",
                 color_continuous_scale="RdYlGn_r",
                 labels={"delay_pct": "Delay %", "iata_code": "Airport"})
    st.plotly_chart(fig, width="stretch")
    st.dataframe(df_pct, width="stretch")

# ══════════════════════════════════════════════════════════════
# PAGE 5 — Route Leaderboards
# ══════════════════════════════════════════════════════════════
elif page == "🏆 Route Leaderboards":
    st.title("🏆 Route Leaderboards")
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔥 Busiest Routes")
        df_routes = run_query("""
            SELECT origin_iata, destination_iata,
                   COUNT(*) AS total_flights
            FROM flights
            WHERE origin_iata IS NOT NULL
              AND destination_iata IS NOT NULL
            GROUP BY origin_iata, destination_iata
            ORDER BY total_flights DESC
            LIMIT 15
        """)
        df_routes["route"] = df_routes["origin_iata"] + " → " + df_routes["destination_iata"]
        fig = px.bar(df_routes, x="total_flights", y="route",
                     orientation="h", color="total_flights",
                     color_continuous_scale="Blues")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.subheader("😴 Most Delayed Airports")
        df_del = run_query("""
            SELECT airport_iata,
                   avg_delay_min, delayed_flights, canceled_flights
            FROM airport_delays
            ORDER BY avg_delay_min DESC
        """)
        fig = px.bar(df_del, x="airport_iata", y="avg_delay_min",
                     color="canceled_flights",
                     labels={"avg_delay_min": "Avg Delay (min)",
                             "airport_iata": "Airport"},
                     color_continuous_scale="Reds")
        st.plotly_chart(fig, width="stretch")

    st.subheader("Top Airports by Total Flights")
    df_top = run_query("""
        SELECT iata_code, name,
               departures + arrivals AS total
        FROM (
            SELECT a.iata_code, a.name,
                   SUM(CASE WHEN f.origin_iata      = a.iata_code THEN 1 ELSE 0 END) AS departures,
                   SUM(CASE WHEN f.destination_iata = a.iata_code THEN 1 ELSE 0 END) AS arrivals
            FROM airport a
            LEFT JOIN flights f ON f.origin_iata = a.iata_code
                                OR f.destination_iata = a.iata_code
            GROUP BY a.iata_code, a.name
        ) sub
        ORDER BY total DESC
        LIMIT 10
    """)
    st.dataframe(df_top, width="stretch")

# ══════════════════════════════════════════════════════════════
# PAGE 6 — SQL Query Results
# ══════════════════════════════════════════════════════════════
elif page == "📊 SQL Query Results":
    st.title("📊 SQL Query Results")
    st.markdown("All 11 required project queries with results.")
    st.divider()

    queries = {
        "Q1: Flights per Aircraft Model": """
            SELECT ac.model, COUNT(f.flight_id) AS total_flights
            FROM flights f JOIN aircraft ac ON f.aircraft_registration = ac.registration
            GROUP BY ac.model ORDER BY total_flights DESC
        """,
        "Q2: Aircraft with >5 Flights": """
            SELECT ac.registration, ac.model, COUNT(f.flight_id) AS flight_count
            FROM flights f JOIN aircraft ac ON f.aircraft_registration = ac.registration
            GROUP BY ac.registration, ac.model HAVING flight_count > 5
            ORDER BY flight_count DESC
        """,
        "Q3: Airports with >5 Outbound Flights": """
            SELECT a.name, a.iata_code, COUNT(f.flight_id) AS outbound
            FROM flights f JOIN airport a ON f.origin_iata = a.iata_code
            GROUP BY a.iata_code, a.name HAVING outbound > 5
            ORDER BY outbound DESC
        """,
        "Q4: Top 3 Destination Airports": """
            SELECT a.name, a.city, COUNT(f.flight_id) AS arrivals
            FROM flights f JOIN airport a ON f.destination_iata = a.iata_code
            GROUP BY a.iata_code, a.name, a.city
            ORDER BY arrivals DESC LIMIT 3
        """,
        "Q5: Domestic vs International": """
            SELECT f.flight_number, f.origin_iata, f.destination_iata,
                   CASE WHEN a1.country = a2.country THEN 'Domestic'
                        ELSE 'International' END AS flight_type
            FROM flights f
            LEFT JOIN airport a1 ON f.origin_iata = a1.iata_code
            LEFT JOIN airport a2 ON f.destination_iata = a2.iata_code
            LIMIT 100
        """,
        "Q6: 5 Recent Arrivals at DEL": """
            SELECT f.flight_number, f.aircraft_registration,
                   COALESCE(a.name, f.origin_iata) AS departure_airport,
                   f.actual_arrival
            FROM flights f LEFT JOIN airport a ON f.origin_iata = a.iata_code
            WHERE f.destination_iata = 'DEL' AND f.actual_arrival IS NOT NULL
            ORDER BY f.actual_arrival DESC LIMIT 5
        """,
        "Q7: Airports with No Arrivals": """
            SELECT a.name, a.iata_code, a.city, a.country FROM airport a
            WHERE a.iata_code NOT IN (
                SELECT DISTINCT destination_iata FROM flights
                WHERE destination_iata IS NOT NULL)
        """,
        "Q8: Flights by Airline & Status": """
            SELECT f.airline_name,
                   SUM(CASE WHEN f.status IN ('Arrived','Departed') THEN 1 ELSE 0 END) AS on_time,
                   SUM(CASE WHEN f.status='Delayed'  THEN 1 ELSE 0 END) AS 'delayed',
                   SUM(CASE WHEN f.status='Canceled' THEN 1 ELSE 0 END) AS canceled,
                   SUM(CASE WHEN f.status='Expected' THEN 1 ELSE 0 END) AS expected,
                   COUNT(*) AS total
            FROM flights f WHERE f.airline_name IS NOT NULL AND f.airline_name != ''
            GROUP BY f.airline_name ORDER BY total DESC LIMIT 20
        """,
        "Q9: Cancelled Flights": """
            SELECT f.flight_number, f.aircraft_registration,
                   COALESCE(a1.name, f.origin_iata) AS origin,
                   COALESCE(a2.name, f.destination_iata) AS destination,
                   f.scheduled_departure
            FROM flights f
            LEFT JOIN airport a1 ON f.origin_iata = a1.iata_code
            LEFT JOIN airport a2 ON f.destination_iata = a2.iata_code
            WHERE f.status = 'Canceled'
            ORDER BY f.scheduled_departure DESC LIMIT 20
        """,
        "Q10: City Pairs with >2 Aircraft Models": """
            SELECT f.origin_iata, f.destination_iata,
                   COUNT(DISTINCT COALESCE(ac.model, f.aircraft_registration)) AS models
            FROM flights f LEFT JOIN aircraft ac ON f.aircraft_registration = ac.registration
            WHERE f.aircraft_registration IS NOT NULL
            GROUP BY f.origin_iata, f.destination_iata HAVING models > 2
            ORDER BY models DESC LIMIT 20
        """,
        "Q11: Delay % per Destination Airport": """
            SELECT a.name, a.iata_code, COUNT(f.flight_id) AS total,
                   SUM(CASE WHEN f.status='Delayed' THEN 1 ELSE 0 END) AS 'delayed',
                   ROUND(SUM(CASE WHEN f.status='Delayed' THEN 1 ELSE 0 END)*100.0/COUNT(f.flight_id),2) AS pct
            FROM flights f JOIN airport a ON f.destination_iata = a.iata_code
            GROUP BY a.iata_code, a.name HAVING total > 0
            ORDER BY pct DESC
        """
    }

    selected_q = st.selectbox("Select Query", list(queries.keys()))
    df_result = run_query(queries[selected_q])
    st.markdown(f"**{len(df_result)} rows returned**")
    st.dataframe(df_result, width="stretch")

    if len(df_result) > 0 and df_result.select_dtypes(include="number").shape[1] > 0:
        num_col = df_result.select_dtypes(include="number").columns[0]
        str_col = df_result.select_dtypes(include="object").columns[0] if df_result.select_dtypes(include="object").shape[1] > 0 else None
        if str_col:
            fig = px.bar(df_result.head(20), x=str_col, y=num_col, color=num_col,
                         color_continuous_scale="Viridis")
            st.plotly_chart(fig, width="stretch")