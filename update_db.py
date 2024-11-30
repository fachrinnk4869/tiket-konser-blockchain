import sqlite3


def update_transactions_to_pending(db_path):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Update all transactions to 'pending'
        cursor.execute("UPDATE transactions SET status = 'pending'")

        # Commit the changes
        conn.commit()
        print("All transactions have been updated to 'pending'.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the connection
        if conn:
            conn.close()


if __name__ == "__main__":
    db_path = 'tickets.db'  # Update this path to your database file
    update_transactions_to_pending(db_path)
