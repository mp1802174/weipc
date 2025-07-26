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

print("=== Target Forum (FID=2) ===")
cursor.execute("SELECT fid, name, threads, posts FROM pre_forum_forum WHERE fid = 2")
forum = cursor.fetchone()
if forum:
    print(f"FID: {forum[0]}, Name: {forum[1]}, Threads: {forum[2]}, Posts: {forum[3]}")
else:
    print("Forum FID=2 not found")

print("\n=== Target User (UID=4) ===")
cursor.execute("SELECT uid, username, posts FROM pre_common_member WHERE uid = 4")
user = cursor.fetchone()
if user:
    print(f"UID: {user[0]}, Username: {user[1]}, Posts: {user[2]}")
else:
    print("User UID=4 not found")

print("\n=== Current Max IDs ===")
cursor.execute("SELECT MAX(tid) FROM pre_forum_thread")
max_tid = cursor.fetchone()[0]
print(f"Max TID: {max_tid}")

cursor.execute("SELECT MAX(pid) FROM pre_forum_post")
max_pid = cursor.fetchone()[0]
print(f"Max PID: {max_pid}")

conn.close()
