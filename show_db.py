import sqlite3

conn = sqlite3.connect('data/pallavi.db')
cursor = conn.cursor()

print('=== Recent 20 Tickets (Latest First) ===\n')
cursor.execute('SELECT ticket_id, mobile, issue_type, issue, status, created_at FROM tickets ORDER BY created_at DESC LIMIT 20')
rows = cursor.fetchall()

for i, row in enumerate(rows, 1):
    vid, mobile, issue_type, issue, status, created = row
    print(f'{i}. Ticket: {vid}')
    print(f'   Mobile: {mobile}')
    print(f'   Type: {issue_type}')
    issue_text = (issue[:60] + '...') if issue and len(issue) > 60 else (issue or 'N/A')
    print(f'   Issue: {issue_text}')
    print(f'   Status: {status}')
    print(f'   Created: {created}')
    print()

conn.close()
