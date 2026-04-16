import requests
import json
import sqlite3

# Test 1: Simulate incoming call
print('[TEST 1] Simulate incoming call...')
r1 = requests.post('http://127.0.0.1:8000/incoming-call', data={
    'CallSid': 'SIM-VOICE-001',
    'From': '+919843398325'
})
print(f'  Status: {r1.status_code}')
print(f'  Response: {r1.text[:150]}' if len(r1.text) > 150 else f'  Response: {r1.text}')

# Test 2: Simulate user speech processing
print('\n[TEST 2] Simulate user speech (issue description)...')
r2 = requests.post('http://127.0.0.1:8000/simulate-recording', json={
    'text': 'There is a pothole on MG Road near the metro station causing traffic jams',
    'call_id': 'SIM-VOICE-001'
})
print(f'  Status: {r2.status_code}')
resp_text = json.dumps(r2.json(), indent=2)
print(f'  Response: {resp_text[:400]}')

# Test 3: Check if ticket was created
print('\n[TEST 3] Checking if ticket was created in database...')
conn = sqlite3.connect('data/pallavi.db')
cursor = conn.cursor()
cursor.execute("SELECT ticket_id, mobile, issue, department FROM tickets WHERE call_id = 'SIM-VOICE-001' LIMIT 1")
result = cursor.fetchone()

if result:
    print(f'  ✅ TICKET CREATED: {result[0]}')
    print(f'     Mobile: {result[1]}')
    print(f'     Issue: {result[2]}')
    print(f'     Department: {result[3]}')
else:
    print('  ❌ No ticket found yet')

conn.close()
