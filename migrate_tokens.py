import sqlite3

db_path = "sql_app.db"
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE chat_messages ADD COLUMN input_tokens INTEGER;")
    cursor.execute("ALTER TABLE chat_messages ADD COLUMN output_tokens INTEGER;")
    conn.commit()
    conn.close()
    print("Migration successful: added input_tokens and output_tokens to chat_messages.")
except Exception as e:
    print(f"Migration result: {e}")
