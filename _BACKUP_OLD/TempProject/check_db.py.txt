import sqlite3

def check():
    conn = sqlite3.connect("crm.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads")
    rows = cursor.fetchall()
    print(f"[*] В базе сейчас {len(rows)} записей.")
    for row in rows[:5]:
        print(row)
    conn.close()

if __name__ == "__main__":
    check()