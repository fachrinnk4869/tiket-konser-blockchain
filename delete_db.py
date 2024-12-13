import sqlite3


def delete_all_transactions():
    # Connect to the SQLite database
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()

    # Delete all records from the tickets table
    cursor.execute("DELETE FROM transactions")
    cursor.execute("DELETE FROM tickets")

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


if __name__ == "__main__":
    delete_all_transactions()
    print("All transactions have been deleted.")
