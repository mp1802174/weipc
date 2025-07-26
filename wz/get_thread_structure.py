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

print("=== pre_forum_thread table structure ===")
cursor.execute("DESCRIBE pre_forum_thread")
for row in cursor.fetchall():
    print(f"{row[0]:20} {row[1]:30} {row[2]:5} {row[3]:10} {str(row[4]):15}")

print("\n=== Sample thread data ===")
cursor.execute("SELECT tid, fid, subject, author, authorid, dateline FROM pre_forum_thread LIMIT 2")
for row in cursor.fetchall():
    print(f"TID: {row[0]}, FID: {row[1]}, Subject: {row[2]}, Author: {row[3]}, AuthorID: {row[4]}, Date: {row[5]}")

conn.close()
