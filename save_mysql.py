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
# Hàm tạo bảng nếu chưa có (và thêm cột role nếu thiếu)
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

        # Tạo bảng nếu chưa có
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                role ENUM('user','admin') DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Bảng `users` đã sẵn sàng!")

        # Kiểm tra xem cột role có tồn tại chưa
        cursor.execute("SHOW COLUMNS FROM users LIKE 'role'")
        result = cursor.fetchone()
        if not result:
            cursor.execute("ALTER TABLE users ADD COLUMN role ENUM('user','admin') DEFAULT 'user'")
            print("🔧 Đã thêm cột `role` vào bảng `users`.")

    except Error as e:
        print("❌ Lỗi khi tạo bảng:", e)



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

# Hàm thêm user (mặc định role = user)
def insert_new_user(username, email, password):
    """Thêm user mới với role mặc định là 'user'."""
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        sql = "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (username, email, password, "user"))  # mặc định role = user
        connection.commit()
        print("✅ Thêm user mới thành công (role=user)!")
        return True
    except Error as e:
        print("❌ Lỗi khi thêm user:", e)
        return False


        
# Hàm đăng nhập user
def login_user(email, password):
    """Kiểm tra email và password, role"""
    connection = connect_to_mysql()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)  # trả về dict thay vì tuple
        sql = "SELECT * FROM users WHERE email = %s AND password = %s"
        cursor.execute(sql, (email, password))
        result = cursor.fetchone()
        if result:
            print(f"✅ Đăng nhập thành công! Xin chào {result['username']} (role={result['role']})")
        else:
            print("❌ Đăng nhập thất bại!")
        return result
    except Error as e:
        print("❌ Lỗi khi kiểm tra user:", e)
        return None



#////////////////////// ADMIN//////////////////////
 ## Thêm user mới với quyền admin.
def admin_insert_user(username, email, password, role):
    connection = connect_to_mysql()
    if connection is None:
        return False, "Lỗi kết nối CSDL"

    try:
        cursor = connection.cursor()
        sql = "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (username, email, password, role))
        connection.commit()
        return True, f"Thêm user '{username}' thành công (role={role})!"
    except Error as e:
        return False, f"Lỗi khi thêm user: {e}"

        
# Hàm update thông tin user
def update_user(user_id, username, email, password, role):
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        sql = """
            UPDATE users
            SET username = %s, email = %s, password = %s, role = %s
            WHERE id = %s
        """
        cursor.execute(sql, (username, email, password, role, user_id))
        connection.commit()

        if cursor.rowcount > 0:
            print(f"✅ User ID {user_id} đã được cập nhật!")
            return True
        else:
            print(f"⚠️ Không tìm thấy user ID {user_id} để cập nhật.")
            return False
    except Error as e:
        print("❌ Lỗi khi update user:", e)
        return False



# Hàm xóa user
def delete_user(user_id):
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        sql = "DELETE FROM users WHERE id = %s"
        cursor.execute(sql, (user_id,))
        connection.commit()

        if cursor.rowcount > 0:
            print(f"🗑️ User ID {user_id} đã bị xóa!")
            return True
        else:
            print(f"⚠️ Không tìm thấy user ID {user_id} để xóa.")
            return False
    except Error as e:
        print("❌ Lỗi khi xóa user:", e)
        return False


# Hàm xem toàn bộ người dùng trong bảng users
def show_all_users():
    """Lấy tất cả user trong bảng users."""
    connection = connect_to_mysql()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)  # trả về dạng dict
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        print(f"👥 Tìm thấy {len(rows)} user.")
        return rows if rows else []

    except Error as e:
        print("❌ Lỗi khi truy vấn dữ liệu:", e)
        return None

# Hàm lấy toàn bộ dữ liệu tất cả bảng trong database
def get_all_tables_data():
    """Lấy toàn bộ dữ liệu tất cả bảng trong database."""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            all_data = []

            for table in tables:
                # key tên cột của dict trả về tùy driver, nên lấy value đầu tiên
                table_name = list(table.values())[0] if isinstance(table, dict) else table[0]
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                all_data.append({
                    "table": table_name,
                    "columns": list(rows[0].keys()) if rows else [],
                    "rows": rows
                })
            print(f"✅ Lấy dữ liệu từ {len(tables)} bảng thành công.")
            return all_data
    except Error as e:
        print(f"Lỗi: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


# # Test
# if __name__ == "__main__":
#     create_database()   # 🔹 tạo DB nếu chưa có
#     create_table()      # 🔹 tạo bảng nếu chưa có
#     # insert_new_user("bao", "bao123@gmail.com", "123")
#     # login_user("hoang123@gmail.com", "123456")
#     show_all_users()