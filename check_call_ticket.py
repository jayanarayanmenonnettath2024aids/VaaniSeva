import sqlite3

# Check for tickets with call_id matching our test call
call_id = 'CA33e43c7d0d4756d04ab337655099bc92'

conn = sqlite3.connect('data/pallavi.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM tickets WHERE call_id = ?", (call_id,))
result = cursor.fetchone()

if result:
    print(f"✅ TICKET FOUND FOR CALL {call_id}")
    print(f"Ticket ID: {result[0]}")
    print(f"Mobile: {result[3]}")
    print(f"Issue: {result[4]}")
    print(f"Department: {result[6]}")
    print(f"Status: {result[7]}")
else:
    print(f"❌ No ticket found for call {call_id}")
    print("\n📋 Latest 3 tickets (any call_id):")
    cursor.execute("SELECT ticket_id, call_id, mobile, issue, department, status FROM tickets ORDER BY rowid DESC LIMIT 3")
    for row in cursor.fetchall():
        print(f"  TID: {row[0]}, CallID: {row[1]}, Mobile: {row[2]}")
        print(f"    Issue: {row[3]}, Dept: {row[4]}, Status: {row[5]}")

conn.close()
