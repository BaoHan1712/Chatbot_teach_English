from save_mysql import *

# Khởi tạo database và bảng khi server start

def add_admin_first(username, email, password, role="admin"):
    connection = connect_to_mysql()
    if connection is None:
        return False, "❌ Lỗi kết nối CSDL"

    try:
        cursor = connection.cursor()
        sql = """
            INSERT IGNORE INTO users (username, email, password, role)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (username, email, password, role))
        connection.commit()

        if cursor.rowcount == 0:
            return False, f"⚠️ User '{username}' hoặc email '{email}' đã tồn tại, bỏ qua."
        else:
            return True, f"✅ Thêm admin '{username}' thành công!"
    except Error as e:
        return False, f"❌ Lỗi khi thêm user: {e}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("🔌 Đã đóng kết nối MySQL.")

def startup():
    create_database()
    create_table()
    add_admin_first("admin12", "admi22n@gmail.com", "admin123")
    print("✅ Database và bảng đã được khởi tạo, admin mặc định đã được thêm.")
    # show_all_users()

# startup()
