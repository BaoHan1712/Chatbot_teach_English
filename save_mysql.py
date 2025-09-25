import mysql.connector
from mysql.connector import Error

# Cấu hình
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "hoang123@"
DB_NAME = "aichat"

# Hàm tạo database nếu chưa có
def create_database():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print(f"✅ Database `{DB_NAME}` đã sẵn sàng!")
    except Error as e:
        print("❌ Lỗi khi tạo database:", e)


# Hàm tạo bảng nếu chưa có
def create_table():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Bảng `users` đã sẵn sàng!")
    except Error as e:
        print("❌ Lỗi khi tạo bảng:", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Hàm kết nối MySQL
def connect_to_mysql():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        if connection.is_connected():
            print("✅ Kết nối MySQL thành công!")
            return connection
    except Error as e:
        print("❌ Lỗi kết nối MySQL:", e)
    return None

# Hàm thêm user
def insert_new_user(username, email, password):
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        sql = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, email, password))
        connection.commit()
        print("✅ Thêm user mới thành công!")
        return True
    except Error as e:
        print("❌ Lỗi khi thêm user:", e)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("🔌 Đã đóng kết nối MySQL.")

# Test
if __name__ == "__main__":
    create_database()   # 🔹 tạo DB nếu chưa có
    create_table()      # 🔹 tạo bảng nếu chưa có
    insert_new_user("hoang", "hoang123@gmail.com", "123456")