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

print("=== pre_forum_post table structure ===")
cursor.execute("DESCRIBE pre_forum_post")
for row in cursor.fetchall():
    print(f"{row[0]:20} {row[1]:30} {row[2]:5} {row[3]:10} {str(row[4]):15}")

print("\n=== Sample post data ===")
cursor.execute("SELECT pid, tid, first, subject, author, authorid, dateline FROM pre_forum_post WHERE first = 1 LIMIT 2")
for row in cursor.fetchall():
    print(f"PID: {row[0]}, TID: {row[1]}, First: {row[2]}, Subject: {row[3]}, Author: {row[4]}, AuthorID: {row[5]}, Date: {row[6]}")

conn.close()
