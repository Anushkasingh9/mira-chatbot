import mysql.connector
from mysql.connector import Error


# Safe connection per function call
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Anushka@2508",
        database="pandeyji_eatery"
    )


def insert_order_item(food_item, quantity, order_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 🛠 Call stored procedure from your DB
        cursor.callproc("insert_order_item", [food_item, quantity, order_id])

        conn.commit()
        cursor.close()
        conn.close()
        return 1

    except Error as err:
        print(f"[insert_order_item] MySQL error: {err}")
        return -1

    except Exception as e:
        print(f"[insert_order_item] Exception: {e}")
        return -1


def insert_order_tracking(order_id, status):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
        cursor.execute(query, (order_id, status))
        conn.commit()
        cursor.close()
        conn.close()
    except Error as err:
        print(f"[insert_order_tracking] MySQL error: {err}")
    except Exception as e:
        print(f"[insert_order_tracking] Exception: {e}")


def get_total_order_price(order_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT get_total_order_price(%s)"
        cursor.execute(query, (order_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result and result[0] is not None and result[0] >= 0 else 0
    except Error as err:
        print(f"[get_total_order_price] MySQL error: {err}")
        return 0
    except Exception as e:
        print(f"[get_total_order_price] Exception: {e}")
        return 0


def get_next_order_id():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT MAX(order_id) FROM order_tracking"
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return 1 if result[0] is None else result[0] + 1
    except Error as err:
        print(f"[get_next_order_id] MySQL error: {err}")
        return 1
    except Exception as e:
        print(f"[get_next_order_id] Exception: {e}")
        return 1


def get_order_status(order_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT status FROM order_tracking WHERE order_id = %s"
        cursor.execute(query, (order_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else None
    except Error as err:
        print(f"[get_order_status] MySQL error: {err}")
        return None
    except Exception as e:
        print(f"[get_order_status] Exception: {e}")
        return None


# For debugging only
if __name__ == "__main__":
    print(get_next_order_id())
