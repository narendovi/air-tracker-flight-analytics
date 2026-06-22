import mysql.connector

try:
    conn = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="your_mysql_password_here"
    )
    print("Connected successfully!")
    conn.close()
except mysql.connector.Error as e:
    print(f"Connection failed: {e}")