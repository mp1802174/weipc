import mysql.connector

conn = mysql.connector.connect(
    host='140.238.201.162',
    port=3306,
    user='00077',
    password='760516',
    database='00077',
    charset='utf8mb4'
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM pre_forum_thread")
print("Thread count:", cursor.fetchone()[0])
conn.close()
print("Test completed")
