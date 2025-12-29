import mysql.connector
from unidecode import unidecode
import re

def update_search_names():
    try:
        # Kết nối Database
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='gemini_user',
            password='123456',
            database='gemini_shop'
        )
        cursor = conn.cursor()

        # 1. Kiểm tra xem cột search_name đã tồn tại chưa, nếu chưa thì tạo
        cursor.execute("SHOW COLUMNS FROM products LIKE 'search_name'")
        if not cursor.fetchone():
            print("Đang thêm cột search_name vào bảng products...")
            cursor.execute("ALTER TABLE products ADD COLUMN search_name VARCHAR(255)")

        # 2. Lấy dữ liệu tên gốc
        cursor.execute("SELECT id, name FROM products")
        products = cursor.fetchall()

        # 3. Chuyển đổi và cập nhật
        for (prod_id, prod_name) in products:
            clean_name = unidecode(prod_name).lower() # "Áo Thun" -> "ao thun"
            clean_name = re.sub(r'[^a-z0-9\s]', ' ', clean_name)
            clean_name = ' '.join(clean_name.split())
            cursor.execute(
                "UPDATE products SET search_name = %s WHERE id = %s",
                (clean_name, prod_id)
            )
        
        conn.commit()
        print(f"Thành công! Đã cập nhật {len(products)} sản phẩm.")

    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    update_search_names()

# Mỗi khi bạn thêm sản phẩm mới bằng tay vào database
#, hãy chạy lệnh này trong Terminal:
# python3 script_update_db.py