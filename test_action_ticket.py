import requests
import json
import sqlite3

payload = {
    'call_id': 'TEST-ACTION-001',
    'structured_data': {
        'customer_name': '',
        'mobile': '+919843398325',
        'issue': 'Pothole on MG Road',
        'location': 'MG Road, Bangalore',
        'issue_type': 'Road'
    }
}

print('[TEST] Creating ticket via action endpoint...')
r = requests.post('http://127.0.0.1:8000/process-action', json=payload, timeout=10)
print(f'Status: {r.status_code}')
print(f'Response: {json.dumps(r.json(), indent=2)}')

# Check if ticket was created
conn = sqlite3.connect('data/pallavi.db')
cursor = conn.cursor()
cursor.execute("SELECT ticket_id, mobile, issue FROM tickets WHERE call_id = 'TEST-ACTION-001' LIMIT 1")
result = cursor.fetchone()

if result:
    print(f'\n✅ TICKET CREATED: {result}')
else:
    print('\n❌ No ticket created')

conn.close()
