# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import mysql.connector
from unidecode import unidecode
import re
from thefuzz import fuzz, process
import json

# Tạo một function dùng chung ở đầu file
def get_db_connection():
    try:
        return mysql.connector.connect(
            host='127.0.0.1',
            user='gemini_user',
            password='123456',
            database='gemini_shop'
        )
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def get_id(cursor, type_input, data):
    """
    Trả về ID và tên chuẩn dựa trên loại đầu vào.
    - type_input: 'loai', 'hang', 'san_pham', 'sku'
    - data: chuỗi tìm kiếm
    Returns: type_input, id_output, name_output, error_msg
    """
    if not data:
        return type_input, None, None, "Dữ liệu đầu vào trống."

    search_term = unidecode(str(data)).lower().strip()
    
    # Cấu hình bảng và cột dựa trên type_input
    config = {
        'loai': {
            'table': 'DANHMUC',
            'id_col': 'id_loai',
            'name_col': 'ten_loai'
        },
        'hang': {
            'table': 'THUONGHIEU',
            'id_col': 'id_thuonghieu',
            'name_col': 'ten' # Theo schema bạn cung cấp: THUONGHIEU.ten
        },
        'san_pham': {
            'table': 'SPCHINH',
            'id_col': 'id_sp',
            'name_col': 'ten'
        },
        'sku': {
            'table': 'BIENTHESP',
            'id_col': 'id_bienthe',
            'name_col': 'sku'
        }
    }

    if type_input not in config:
        return type_input, None, None, f"Loại tìm kiếm '{type_input}' không hợp lệ."

    cfg = config[type_input]
    
    try:
        # --- BƯỚC 1: SQL LIKE (Tìm nhanh) ---
        query_like = f"SELECT {cfg['id_col']}, {cfg['name_col']} FROM {cfg['table']} WHERE {cfg['name_col']} LIKE %s"
        cursor.execute(query_like, (f"%{data}%",))
        result = cursor.fetchone()

        if result:
            return type_input, result[cfg['id_col']], result[cfg['name_col']], None

        # --- BƯỚC 2: THEFUZZ (Tìm mờ nếu LIKE thất bại) ---
        cursor.execute(f"SELECT {cfg['id_col']}, {cfg['name_col']} FROM {cfg['table']}")
        all_rows = cursor.fetchall()

        if all_rows:
            # Tạo dictionary để so khớp mờ
            choices = {unidecode(row[cfg['name_col']]).lower(): row for row in all_rows}
            best_match = process.extractOne(search_term, choices.keys(), scorer=fuzz.token_set_ratio)

            if best_match and best_match[1] >= 75: # Ngưỡng tin cậy 75%
                matched_row = choices[best_match[0]]
                return type_input, matched_row[cfg['id_col']], matched_row[cfg['name_col']], None

        return type_input, None, None, f"Không tìm thấy {type_input} nào khớp với '{data}'."

    except Exception as e:
        return type_input, None, None, f"Lỗi truy vấn: {str(e)}"

# HÀM HELPER CHÍNH: Tìm kiếm sản phẩm thông minh
def find_products_in_db(tracker, cursor, type_input, data_input):
    """
    Sử dụng hàm get_id để tìm ID sản phẩm hoặc biến thể.
    - type_input: 'product_name' hoặc 'product_bienthe' (map sang 'san_pham' hoặc 'sku' trong get_id)
    - data_input: giá trị chuỗi khách nhập
    Returns: raw_data, type_input, id_output, error_msg
    """
    if not data_input:
        return data_input, type_input, None, "Dữ liệu đầu vào trống."

    # 1. Map type_input từ Rasa sang type_input của hàm get_id
    mapping = {
        'product_name': 'san_pham',
        'product_bienthe': 'sku'
    }
    
    internal_type = mapping.get(type_input)
    if not internal_type:
        return data_input, type_input, None, f"Kiểu lọc '{type_input}' không hợp lệ."

    # 2. Gọi hàm get_id để xử lý LIKE và Fuzzy Matching
    # Hàm get_id trả về: type_in, id_out, name_out, err
    _, id_output, name_output, error_msg = get_id(cursor, internal_type, data_input)

    # 3. Trả về kết quả theo định dạng find_products_in_db cũ để không làm gãy các Action phía trên
    if (error_msg or not id_output) and type_input=='product_bienthe':
        type_input = 'product_name'
        internal_type = mapping.get(type_input)
        _, id_output, name_output, error_msg = get_id(cursor, internal_type, data_input)

    if error_msg:
        return data_input, type_input, None, error_msg
        
    return name_output, type_input, id_output, None

def get_product_view_by_id(cursor, id_sp):
    """
    Hàm nhận id_sp và trả về toàn bộ biến thể kèm thông tin chi tiết từ VIEW
    """
    try:
        # Truy vấn trực tiếp từ VIEW đã tạo
        query = "SELECT * FROM view_chi_tiet_san_pham WHERE id_sp = %s"
        cursor.execute(query, (id_sp,))
        
        # Lấy tất cả các biến thể của sản phẩm đó (ví dụ: các màu, các mức dung lượng)
        results = cursor.fetchall()
        
        if not results:
            return None, "Không tìm thấy dữ liệu chi tiết cho sản phẩm này."
            
        return results, None

    except Exception as e:
        return None, f"Lỗi truy vấn VIEW: {str(e)}"

def count_product_by_thuonghieu(cursor, thuonghieu_input):
    """
    Sử dụng get_id để chuẩn hóa thương hiệu, sau đó đếm số sản phẩm chính từ VIEW.
    Returns: id_th, ten_th, so_luong, list_sp, error
    """
    if not thuonghieu_input:
        return None, None, 0, [], "Dữ liệu đầu vào trống."

    try:
        # --- BƯỚC 1: CHUẨN HÓA THƯƠNG HIỆU QUA HÀM GET_ID ---
        # Hàm get_id đã bao gồm cả SQL LIKE và TheFuzz
        _, id_th, ten_th, error_msg = get_id(cursor, 'hang', thuonghieu_input)

        if error_msg or not id_th:
            return None, None, 0, [], error_msg

        # --- BƯỚC 2: TRUY VẤN SẢN PHẨM DỰA TRÊN ID THƯƠNG HIỆU ---
        # Sử dụng id_thuonghieu (integer) giúp truy vấn nhanh hơn nhiều so với LIKE tên
        query_sp = "SELECT DISTINCT id_sp, ten_san_pham FROM view_chi_tiet_san_pham WHERE ten_thuonghieu = %s"
        cursor.execute(query_sp, (ten_th,))
        list_results = cursor.fetchall()

        if not list_results:
            return id_th, ten_th, 0, [], None

        list_sanpham = [item['ten_san_pham'] for item in list_results]
        so_luong = len(list_sanpham)

        return id_th, ten_th, so_luong, list_sanpham, None

    except Exception as e:
        print(f"Error in count_product_by_thuonghieu: {e}")
        return None, None, 0, [], f"Lỗi hệ thống khi thống kê sản phẩm."

def count_thuonghieu_by_type(cursor, loai_input):
    """
    Sử dụng get_id để tìm ID danh mục và trả về danh sách thương hiệu tương ứng.
    Returns: id_loai, ten_loai, so_luong_th, list_ten_th, error
    """
    if not loai_input:
        return None, None, 0, [], "Dữ liệu đầu vào trống."

    try:
        # --- BƯỚC 1: CHUẨN HÓA DANH MỤC QUA HÀM GET_ID ---
        # Hàm get_id sẽ tự động xử lý SQL LIKE và thefuzz cho bảng DANHMUC
        _, id_loai, ten_loai, error_msg = get_id(cursor, 'loai', loai_input)

        if error_msg or not id_loai:
            return None, None, 0, [], error_msg

        # --- BƯỚC 2: TRUY VẤN THƯƠNG HIỆU TỪ VIEW ---
        # Sử dụng ten_loai chuẩn từ DB để đảm bảo kết quả chính xác 100%
        query_th = "SELECT DISTINCT ten_thuonghieu FROM view_chi_tiet_san_pham WHERE ten_loai = %s"
        cursor.execute(query_th, (ten_loai,))
        brand_results = cursor.fetchall()

        list_ten_th = [b['ten_thuonghieu'] for b in brand_results]
        so_luong_th = len(list_ten_th)

        return id_loai, ten_loai, so_luong_th, list_ten_th, None

    except Exception as e:
        print(f"Lỗi count_thuonghieu_by_type: {e}")
        return None, None, 0, [], f"Lỗi hệ thống khi truy xuất danh mục."

def search_products_complex(cursor, loai_name=None, hang_name=None, thuoctinh=None, giatri=None):
    """
    Tìm kiếm sản phẩm sử dụng get_id để chuẩn hóa ID và thefuzz để lọc thuộc tính.
    """
    id_loai = None
    id_hang = None
    query = "SELECT * FROM view_chi_tiet_san_pham WHERE 1=1"
    params = []
    
    # --- BƯỚC 1: CHUẨN HÓA ID BẰNG HÀM GET_ID ---
    # --- BƯỚC 2: TRUY VẤN SQL CƠ BẢN ---
    if loai_name:
        _, _, ten_loai_chuan, _ = get_id(cursor, 'loai', loai_name)
        if ten_loai_chuan:
            query += " AND ten_loai = %s"
            params.append(ten_loai_chuan)

    # Xử lý Hãng (Sửa lỗi hang_name ở đây)
    if hang_name:
        _, _, ten_hang_chuan, _ = get_id(cursor, 'hang', hang_name)
        if ten_hang_chuan:
            query += " AND ten_thuonghieu = %s"
            params.append(ten_hang_chuan)
    try:
        cursor.execute(query, tuple(params))
        candidates = cursor.fetchall()

        if not candidates:
            return []

        # --- BƯỚC 3: LỌC THEO THUỘC TÍNH (SỬ DỤNG THEFUZZ) ---
        if thuoctinh and giatri:
            final_results = []
            search_attr = unidecode(str(thuoctinh)).lower().strip()
            search_val = unidecode(str(giatri)).lower().strip()

            for item in candidates:
                # Lấy thuộc tính của biến thể hiện tại
                cursor.execute("SELECT tenthuoctinh, giatri FROM THUOCTINHSP WHERE id_bienthe = %s", (item['id_bienthe'],))
                db_attrs = cursor.fetchall()
                
                for attr in db_attrs:
                    attr_name_norm = unidecode(attr['tenthuoctinh']).lower()
                    attr_val_norm = unidecode(attr['giatri']).lower()
                    
                    # So khớp mờ
                    if (fuzz.token_set_ratio(search_attr, attr_name_norm) >= 80 and 
                        fuzz.token_set_ratio(search_val, attr_val_norm) >= 85):
                        final_results.append(item)
                        break
            return final_results[:10]
        
        return candidates[:10]

    except Exception as e:
        print(f"Lỗi search_products_complex: {e}")
        return []

def find_similar_products(cursor, ten_loai, gia_goc, id_bienthe_goc):
    """
    Tìm sản phẩm cùng loại, trong khoảng giá +/- 20% và loại trừ chính nó.
    """
    gia_goc_float = float(gia_goc)
    # Tính khoảng giá mong muốn
    gia_min = gia_goc_float * 0.8
    gia_max = gia_goc_float * 1.2

    query = """
        SELECT v.* FROM view_chi_tiet_san_pham v
        JOIN DANHMUC d ON v.ten_loai = d.ten_loai
        WHERE v.ten_loai = %s 
          AND v.gia BETWEEN %s AND %s
          AND v.id_bienthe != %s
        ORDER BY ABS(v.gia - %s) ASC
        LIMIT 3
    """
    params = (ten_loai, gia_min, gia_max, id_bienthe_goc, gia_goc_float)
    
    cursor.execute(query, params)
    return cursor.fetchall()

# HÀM HELPER 2: Tạo Button an toàn (Fix lỗi payload)
def create_button(title, intent, entities_dict):
    """
    title: Chữ hiển thị trên nút
    intent: gọi chức năng (vd: 'ask_compare_products', 'ask_show_brand_by_type')
    entities_dict: Dictionary chứa các thực thể đi kèm
    """
    # Tạo payload theo chuẩn: /ask_tên_chức_năng{"entity": "value"}
    payload = f"/{intent}{json.dumps(entities_dict, ensure_ascii=False)}"
    
    return {
        "title": title,
        "payload": payload
    }

def get_product_summary(cursor, id_bienthe, specs_json=None):
    """
    Ưu tiên lấy từ JSON, nếu không có sẽ lấy từ bảng THUOCTINHSP.
    """
    specs_dict = {}

    # 1. Thử giải mã JSON nếu có
    if specs_json:
        try:
            specs_dict = json.loads(specs_json) if isinstance(specs_json, str) else specs_json
        except Exception:
            specs_dict = {}

    # 2. Nếu JSON trống, truy vấn bảng THUOCTINHSP
    if not specs_dict and cursor and id_bienthe:
        query = "SELECT tenthuoctinh, giatri FROM THUOCTINHSP WHERE id_bienthe = %s"
        cursor.execute(query, (id_bienthe,))
        rows = cursor.fetchall()
        # Chuyển list rows thành dict
        specs_dict = {row['tenthuoctinh']: row['giatri'] for row in rows}

    if not specs_dict:
        return "Sản phẩm chính hãng, cấu hình tiêu chuẩn."

    # 3. Format hiển thị
    icon_map = {
        "cpu": "💻 CPU", "ram": "⚡ RAM", "ssd": "💾 Ổ cứng",
        "vga": "🎮 Đồ họa", "screen": "🖥️ Màn hình", "bus": "🚀 Bus",
        "socket": "🔌 Socket", "dung luong": "📦 Dung lượng"
    }

    summary_lines = []
    for key, value in specs_dict.items():
        # Tìm icon phù hợp (xử lý không dấu để map chính xác hơn)
        clean_key = unidecode(key).lower()
        header = icon_map.get(clean_key, f"🔹 {key}")
        summary_lines.append(f"{header}: {value}")

    return "\n".join(summary_lines)

def generate_comparison_table(item1, item2):
    """
    Tạo chuỗi văn bản so sánh giữa 2 sản phẩm.
    """
    # Lấy thông số từ JSON (ưu tiên)
    specs1 = json.loads(item1['thongsokythuat']) if item1['thongsokythuat'] else {}
    specs2 = json.loads(item2['thongsokythuat']) if item2['thongsokythuat'] else {}

    # Danh sách các thuộc tính quan trọng để so sánh
    important_keys = ["CPU", "RAM", "SSD", "VGA", "Screen", "Battery"]
    
    table = f"| Tính năng | {item1['sku']} | {item2['sku']} |\n"
    table += "| :--- | :--- | :--- |\n"
    table += f"| **Giá bán** | {item1['gia']:,}đ | {item2['gia']:,}đ |\n"

    # Lấy tập hợp các key từ cả 2 sản phẩm (không trùng)
    all_keys = list(dict.fromkeys([k.lower() for k in list(specs1.keys()) + list(specs2.keys())]))
    
    for key in all_keys:
        # Chỉ so sánh các key phổ biến để tránh bảng quá dài
        val1 = specs1.get(key, specs1.get(key.upper(), "-"))
        val2 = specs2.get(key, specs2.get(key.upper(), "-"))
        table += f"| {key.capitalize()} | {val1} | {val2} |\n"

    return table



class ActionGetProductPriceSpecs(Action):
    def name(self) -> Text:
        return "action_get_product_price_specs"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cursor = None
        connection = get_db_connection()
        if not connection:
            dispatcher.utter_message(text="⚠️ Lỗi kết nối hệ thống dữ liệu.")
            return []

        try:
            cursor = connection.cursor(dictionary=True)

            # 1. Lấy SKU từ thực thể (entity) người dùng nhập
            sku_input = next(tracker.get_latest_entity_values("product_bienthe"), None)
            if not sku_input:
                sku_input = tracker.get_slot("product_bienthe")

            if not sku_input:
                dispatcher.utter_message(text="❓ Bạn vui lòng cung cấp mã sản phẩm hoặc SKU để mình kiểm tra nhé.")
                return []

            # 2. Sử dụng find_products_in_db để tìm ID biến thể chuẩn
            # Hàm này sẽ xử lý cả SQL LIKE và Fuzzy Matching cho SKU
            sku_standard, type_input, id_bienthe, err = find_products_in_db(tracker, cursor, 'product_bienthe', sku_input)

            if err or not id_bienthe:
                dispatcher.utter_message(text=f"❌ {err}")
                return [SlotSet("product_bienthe", None)]
            
            if type_input == 'product_name':
                message = (
                    f"Dòng sản phẩm **{sku_standard}** có nhiều phiên bản cấu hình khác nhau.\n\n"
                    f"Bạn có muốn xem giới thiệu chung về dòng này hay muốn liệt kê các phiên bản cụ thể?"
                )

                # Sử dụng hàm helper create_button để dẫn khách
                buttons = [
                    # Nút 1: Gọi Action giới thiệu sản phẩm (Bạn đã có)
                    create_button("📖 Xem giới thiệu", "ask_get_product_description", {"product_name": sku_standard}),
                    
                    # Nút 2: Liệt kê các phiên bản (Dùng chung Action xem theo thương hiệu/tên)
                    create_button("📦 Các phiên bản", "ask_show_product_by_brand", {"product_name": sku_standard}),
                    
                    create_button("🔙 Quay lại danh mục", "ask_browse_shop", {})
                ]

                dispatcher.utter_message(text=message, buttons=buttons)
            
                # Vẫn nên lưu lại tên sản phẩm vào slot để giữ ngữ cảnh dòng máy
                return [SlotSet("product_name", sku_standard)]

            # 3. Truy vấn thông tin chi tiết từ VIEW dựa trên id_bienthe
            query = "SELECT * FROM view_chi_tiet_san_pham WHERE id_bienthe = %s"
            cursor.execute(query, (id_bienthe,))
            item = cursor.fetchone()

            if not item:
                dispatcher.utter_message(text="⚠️ Không tìm thấy thông tin chi tiết cho mã sản phẩm này.")
                return []

            # 4. Chuẩn bị nội dung hiển thị
            ten_sp = item['ten_san_pham']
            gia_sp = "{:,.0f}".format(item['gia'])
            hang = item['ten_thuonghieu']
            
            # Sử dụng hàm helper get_product_summary để tạo đoạn text cấu hình
            # Lưu ý: Nếu cột thongsokythuat là JSON, hàm sẽ tự parse
            specs_text = get_product_summary(cursor, item['id_bienthe'], item['thongsokythuat'])

            message = (
                f"🔎 **Thông tin sản phẩm: {ten_sp}**\n"
                f"🏢 Hãng: **{hang}**\n"
                f"🆔 SKU: `{sku_standard}`\n"
                f"💰 Giá bán: **{gia_sp} VNĐ**\n"
                f"--- \n"
                f"⚙️ **Cấu hình chi tiết:**\n"
                f"{specs_text}\n\n"
                f"🛒 Bạn có muốn thêm sản phẩm này vào giỏ hàng không?"
            )

            # 5. Tạo các nút bấm điều hướng tiếp theo (Dùng create_button helper)
            buttons = [
                create_button("🛒 Thêm vào giỏ", "ask_add_to_cart", {"product_bienthe": sku_standard}),
                create_button("💡 Sản phẩm tương tự", "ask_search_similar_products", {"product_bienthe": sku_standard}),
                create_button("🔙 Quay lại danh mục", "ask_show_brand_by_type", {"loai_san_pham": item['ten_loai']})
            ]

            dispatcher.utter_message(text=message, buttons=buttons)

            # Lưu lại SKU vào slot để ghi nhớ ngữ cảnh
            return [SlotSet("product_bienthe", sku_standard)]

        except Exception as e:
            print(f"Lỗi ActionGetProductPriceSpecs: {e}")
            dispatcher.utter_message(text="Hệ thống gặp trục trặc khi tra cứu cấu hình.")
            return []
        
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

class ActionGetProductDescription(Action):
    def name(self) -> Text:
        return "action_get_product_description"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        cursor = None
        connection = get_db_connection()
        if not connection:
            dispatcher.utter_message(text="⚠️ Lỗi kết nối hệ thống dữ liệu.")
            return []

        try:
            cursor = connection.cursor(dictionary=True)

            # 1. Lấy đầu vào từ khách hàng
            raw_input = next(tracker.get_latest_entity_values("product_name"), None)
            if not raw_input:
                raw_input = tracker.get_slot("product_name")

            if not raw_input:
                dispatcher.utter_message(text="❓ Bạn muốn xem thông tin của sản phẩm nào ạ?")
                return []

            # 2. Tìm ID sản phẩm chính (xử lý cả sai chính tả bằng Fuzzy)
            product_standard, _, id_sp_found, error_msg = find_products_in_db(
                tracker, cursor, 'product_name', raw_input
            )

            if error_msg or not id_sp_found:
                msg = (f"Xin lỗi, shop chưa có thông tin về '{raw_input}' ạ.\n"
                       f"Bạn xem qua các danh mục đang sẵn hàng nhé!")
                buttons = [create_button("📦 Xem Shop", "ask_browse_shop", {})]
                dispatcher.utter_message(text=msg, buttons=buttons)
                return [SlotSet("product_name", None)]

            # 3. Lấy tất cả biến thể của sản phẩm này từ VIEW
            results, view_error = get_product_view_by_id(cursor, id_sp_found)

            if view_error or not results:
                dispatcher.utter_message(text="Dữ liệu mô tả sản phẩm đang được cập nhật.")
                return []

            # 4. Trích xuất thông tin chung từ biến thể đầu tiên
            first_item = results[0]
            product_name = first_item['ten_san_pham']
            product_type = first_item['ten_loai']
            brand = first_item['ten_thuonghieu']
            description = first_item.get('mo_ta', 'là dòng sản phẩm chất lượng cao tại shop.')

            # 5. Xây dựng nội dung phản hồi
            msg = (f"📖 **{product_type} {product_name}**\n"
                   f"🏭 Hãng sản xuất: **{brand}**\n\n"
                   f"✨ {description}\n\n"
                   f"👇 **Chọn phiên bản để xem giá và cấu hình chi tiết:**")

            # 6. Tạo danh sách nút bấm SKU (Dùng helper create_button)
            buttons = []
            for item in results:
                v_sku = item['sku']
                # Gửi yêu cầu xem chi tiết SKU cho ActionGetProductPriceSpecs
                buttons.append(create_button(
                    title=f"📎 {v_sku}",
                    intent="ask_get_product_price_specs",
                    entities_dict={"product_bienthe": v_sku}
                ))

            dispatcher.utter_message(text=msg, buttons=buttons[:10])

            # Lưu tên chuẩn vào Slot để dùng cho các câu hỏi sau
            return [SlotSet("product_name", product_name)]

        except Exception as e:
            print(f"Lỗi ActionGetDescription: {e}")
            dispatcher.utter_message(text="Xin lỗi, tôi gặp trục trặc khi tra cứu mô tả sản phẩm.")
            return []
        
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

class ActionShowProductByBrand(Action):
    def name(self) -> Text:
        return "action_show_product_by_brand"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        cursor = None
        connection = get_db_connection()
        if not connection:
            dispatcher.utter_message(text="⚠️ Lỗi kết nối hệ thống dữ liệu.")
            return []

        try:
            cursor = connection.cursor(dictionary=True)

            # 1. Lấy thông tin hãng từ thực thể hoặc Slot
            brand_input = next(tracker.get_latest_entity_values("product_thuonghieu"), None)
            if not brand_input:
                brand_input = tracker.get_slot("product_thuonghieu")

            if not brand_input:
                dispatcher.utter_message(text="❓ Bạn muốn xem sản phẩm của hãng nào ạ?")
                return []

            # 2. Sử dụng helper để chuẩn hóa tên hãng và đếm sản phẩm
            # Trả về: id, tên chuẩn, số lượng, list tên SP, lỗi
            id_th, ten_th, count, products, err = count_product_by_thuonghieu(cursor, brand_input)

            # 3. Xử lý khi không tìm thấy hãng hoặc có lỗi
            if err:
                msg = f"Dạ, {err}\nBạn có muốn xem danh mục khác không?"
                buttons = [create_button("📦 Xem danh mục", "ask_browse_shop", {})]
                dispatcher.utter_message(text=msg, buttons=buttons)
                return [SlotSet("product_thuonghieu", None)]

            if count == 0:
                dispatcher.utter_message(text=f"Hiện tại các mẫu của hãng **{ten_th}** đang hết hàng ạ.")
                return [SlotSet("product_thuonghieu", ten_th)]

            # 4. Xây dựng phản hồi
            msg = f"🏢 Hãng **{ten_th}** đang có **{count}** dòng máy tại shop.\n"
            msg += "Mời bạn chọn sản phẩm để xem mô tả chi tiết:"

            # 5. Tạo nút bấm động bằng helper create_button
            buttons = []
            for p_name in products:
                # Mỗi nút sẽ dẫn tới ActionGetProductDescription
                buttons.append(create_button(
                    title=f"🔍 {p_name}",
                    intent="ask_get_product_description",
                    entities_dict={"product_name": p_name}
                ))

            dispatcher.utter_message(text=msg, buttons=buttons[:10])

            # 6. Ghi nhớ tên hãng chuẩn vào Slot
            return [SlotSet("product_thuonghieu", ten_th)]

        except Exception as e:
            print(f"Lỗi ActionShowProductByBrand: {e}")
            dispatcher.utter_message(text="Xin lỗi, tôi gặp trục trặc khi lấy danh sách sản phẩm.")
            return []
        
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

class ActionShowBrandByType(Action):
    def name(self) -> Text:
        return "action_show_brand_by_type"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        cursor = None
        connection = get_db_connection()
        if not connection:
            dispatcher.utter_message(text="⚠️ Lỗi kết nối hệ thống dữ liệu.")
            return []

        try:
            cursor = connection.cursor(dictionary=True)

            # 1. Lấy thông tin loại sản phẩm từ thực thể hoặc Slot
            type_input = next(tracker.get_latest_entity_values("loai_san_pham"), None)
            if not type_input:
                type_input = tracker.get_slot("loai_san_pham")

            if not type_input:
                dispatcher.utter_message(text="❓ Bạn muốn xem thương hiệu của dòng sản phẩm nào ạ? (VD: Laptop, Chuột...)")
                return []

            # 2. Sử dụng helper để chuẩn hóa loại sản phẩm và đếm thương hiệu
            # Trả về: id_loai, tên chuẩn, số lượng hãng, danh sách hãng, lỗi
            id_loai, ten_loai, count, brands, err = count_thuonghieu_by_type(cursor, type_input)

            # 3. Xử lý khi không tìm thấy loại sản phẩm hoặc lỗi
            if err:
                msg = f"Dạ, {err}\nBạn xem qua các mẫu đang sẵn hàng tại shop nhé!"
                buttons = [create_button("📦 Xem Shop", "ask_browse_shop", {})]
                dispatcher.utter_message(text=msg, buttons=buttons)
                return [SlotSet("loai_san_pham", None)]

            if count == 0:
                dispatcher.utter_message(text=f"Hiện tại shop chưa có hãng nào cho dòng **{ten_loai}**.")
                return [SlotSet("loai_san_pham", ten_loai)]

            # 4. Xây dựng tin nhắn phản hồi
            msg = f"📦 Với dòng **{ten_loai}**, shop đang có sản phẩm từ **{count}** hãng uy tín sau đây:"
            
            # 5. Tạo danh sách nút bấm hãng bằng helper create_button
            buttons = []
            for b_name in brands:
                # Mỗi nút dẫn tới ActionShowProductByBrand
                buttons.append(create_button(
                    title=f"🏢 {b_name}",
                    intent="ask_show_product_by_brand",
                    entities_dict={"product_thuonghieu": b_name}
                ))

            dispatcher.utter_message(text=msg, buttons=buttons[:10])

            # 6. Cập nhật slot để ghi nhớ danh mục chuẩn
            return [SlotSet("loai_san_pham", ten_loai)]

        except Exception as e:
            print(f"Lỗi ActionShowBrandByType: {e}")
            dispatcher.utter_message(text="Xin lỗi, tôi gặp trục trặc khi tra cứu danh mục.")
            return []

        finally:
            if cursor: cursor.close()
            if connection: connection.close()

class ActionBrowseShop(Action):
    def name(self) -> Text:
        return "action_browse_shop"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cursor = None
        connection = get_db_connection()
        if not connection:
            dispatcher.utter_message(text="⚠️ Hệ thống đang bảo trì, bạn vui lòng quay lại sau nhé!")
            return []

        try:
            cursor = connection.cursor(dictionary=True)

            # 1. Thống kê nhanh dữ liệu kho hàng
            # Lấy tổng số biến thể (SKU) đang kinh doanh
            cursor.execute("SELECT COUNT(*) as total FROM BIENTHESP")
            total_count = cursor.fetchone()['total']

            # 2. Lấy danh sách danh mục (Category)
            cursor.execute("SELECT id_loai, ten_loai FROM DANHMUC")
            categories = cursor.fetchall()
            total_types = len(categories)

            if not categories:
                dispatcher.utter_message(text="Dạ, hiện tại shop đang sắp xếp lại kho hàng, chưa có danh mục sẵn sàng ạ.")
                return []

            # 3. Tạo thông điệp chào mừng sống động
            msg = (f"🌟 **Chào mừng bạn đến với Gemini Shop!**\n\n"
                   f"Hiện shop đang có **{total_count}** mã hàng đa dạng "
                   f"thuộc **{total_types}** nhóm sản phẩm.\n"
                   f"Bạn muốn tham khảo dòng sản phẩm nào dưới đây?")

            # 4. Sử dụng helper create_button để tạo nút bấm an toàn
            buttons = []
            for cat in categories:
                cat_name = cat['ten_loai']
                
                # Nút bấm dẫn tới hành động hiển thị hãng theo loại
                buttons.append(create_button(
                    title=f"📦 {cat_name}",
                    intent="ask_show_brand_by_type",
                    entities_dict={"loai_san_pham": cat_name}
                ))

            # 5. Gửi phản hồi (Giới hạn 10 nút đầu tiên để đảm bảo hiển thị tốt trên Mobile/Messenger)
            dispatcher.utter_message(text=msg, buttons=buttons[:10])
            return []

        except Exception as err:
            print(f"Lỗi BrowseShop: {err}")
            dispatcher.utter_message(text="🤖 Oops! Bot gặp chút trục trặc khi lấy danh mục, bạn thử lại sau nhé.")
        
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

        return []

class ActionSearchProductBySpecs(Action):
    def name(self) -> str:
        return "action_search_product_by_specs"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict) -> list:
        
        cursor = None
        connection = get_db_connection()

        if not connection:
            dispatcher.utter_message(text="⚠️ Hệ thống tra cứu đang bận, bạn thử lại sau nhé.")
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)

            # 1. Trích xuất các thực thể từ lời nói của khách hàng
            loai = next(tracker.get_latest_entity_values("loai_san_pham"), None)
            hang = next(tracker.get_latest_entity_values("product_thuonghieu"), None)
            attr_name = next(tracker.get_latest_entity_values("attribute_name"), None)
            attr_value = next(tracker.get_latest_entity_values("attribute_value"), None)

            # 2. Gọi hàm tìm kiếm phức hợp (đã có Fuzzy Matching cho thuộc tính)
            results = search_products_complex(cursor, loai, hang, attr_name, attr_value)

            # 3. Cơ chế Fallback (Nếu không tìm thấy cấu hình chính xác, gợi ý sản phẩm cùng loại/hãng)
            is_fallback = False
            if not results and (attr_name or attr_value):
                results = search_products_complex(cursor, loai, hang)
                if results:
                    is_fallback = True
            
            if not results:
                dispatcher.utter_message(text="Dạ, hiện shop chưa có sản phẩm nào phù hợp với yêu cầu đặc biệt này của bạn ạ.")
                return []

            # 4. Chuẩn bị thông điệp hiển thị
            if is_fallback:
                msg = f"👉 Shop không có mẫu đúng yêu cầu '{attr_value}' rồi, mời bạn xem các mẫu cùng dòng đang sẵn hàng nhé:"
            else:
                msg = "🔍 **Kết quả tìm kiếm phù hợp nhất cho bạn:**"

            buttons = []
            
            for item in results[:5]:
                ten_sp = item['ten_san_pham']
                gia_sp = "{:,.0f}".format(item['gia'])
                sku = item['sku']
                
                msg += f"\n\n✨ **{ten_sp}**\n💰 Giá: **{gia_sp} VNĐ**"
                
                # Sử dụng helper create_button để dẫn khách đến xem chi tiết SKU
                buttons.append(create_button(
                    title=f"Xem cấu hình {sku}",
                    intent="ask_get_product_price_specs",
                    entities_dict={"product_bienthe": sku}
                ))

            buttons.append(create_button("🔙 Quay lại danh mục", "ask_browse_shop", {}))
            dispatcher.utter_message(text=msg, buttons=buttons)
            return []

        except Exception as e:
            print(f"Lỗi SearchSpecs: {e}")
            dispatcher.utter_message(text="Có lỗi xảy ra khi lọc sản phẩm, shop sẽ kiểm tra lại ngay.")
        
        finally:
            if cursor: cursor.close()
            if connection: connection.close()
            
        return []

class ActionCompareProducts(Action):
    def name(self) -> Text:
        return "action_compare_products"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cursor = None
        connection = get_db_connection()
        if not connection: return []

        try:
            cursor = connection.cursor(dictionary=True)
            
            # 1. Lấy danh sách SKU từ entities (Rasa sẽ bắt được list nếu khách nhập 2 cái)
            skus = list(tracker.get_latest_entity_values("product_bienthe"))

            if len(skus) < 2:
                dispatcher.utter_message(text="❓ Để so sánh, bạn vui lòng cung cấp ít nhất 2 mã SKU nhé (Ví dụ: So sánh mã A và mã B).")
                return []

            # 2. Tìm kiếm thông tin chuẩn của cả 2 mã
            results = []
            for s in skus[:2]: # Chỉ so sánh 2 cái đầu tiên
                _, id_bt, sku_std, err = get_id(cursor, 'sku', s)
                if id_bt:
                    cursor.execute("SELECT * FROM view_chi_tiet_san_pham WHERE id_bienthe = %s", (id_bt,))
                    results.append(cursor.fetchone())

            if len(results) < 2:
                dispatcher.utter_message(text="⚠️ Shop không tìm thấy đủ 2 mã sản phẩm bạn yêu cầu để so sánh.")
                return []

            # 3. Tạo bảng so sánh
            item1, item2 = results[0], results[1]
            comparison_table = generate_comparison_table(item1, item2)

            msg = (f"📊 **Bảng so sánh chi tiết**\n\n"
                   f"1️⃣ {item1['ten_san_pham']}\n"
                   f"2️⃣ {item2['ten_san_pham']}\n\n"
                   f"{comparison_table}\n\n"
                   f"Bạn ưng ý mẫu nào hơn ạ?")

            buttons = [
                create_button(f"Chọn {item1['sku']}", "ask_add_to_cart", {"product_bienthe": item1['sku']}),
                create_button(f"Chọn {item2['sku']}", "ask_add_to_cart", {"product_bienthe": item2['sku']})
            ]

            dispatcher.utter_message(text=msg, buttons=buttons)
            return []

        except Exception as e:
            print(f"Lỗi Compare: {e}")
            dispatcher.utter_message(text="Có lỗi xảy ra khi tạo bảng so sánh.")
        
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

        return []

class ActionSearchSimilarProducts(Action):
    def name(self) -> Text:
        return "action_search_similar_products"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cursor = None
        connection = get_db_connection()
        if not connection: 
            dispatcher.utter_message(text="⚠️ Hệ thống bận, không thể gợi ý sản phẩm ngay lúc này.")
            return []

        try:
            cursor = connection.cursor(dictionary=True)

            # 1. Lấy SKU từ Slot (SKU mà khách đang xem hoặc vừa hỏi)
            current_sku = tracker.get_slot("product_bienthe")
            
            if not current_sku:
                # Nếu slot trống, thử lấy từ thực thể cuối cùng người dùng nhắc tới
                current_sku = next(tracker.get_latest_entity_values("product_bienthe"), None)

            if not current_sku:
                dispatcher.utter_message(text="Bạn muốn tìm sản phẩm tương tự với mẫu nào ạ? Hãy cho mình xin mã SKU nhé.")
                return []

            # 2. Lấy thông tin gốc (Dùng View để lấy tên_loai và giá)
            cursor.execute(
                "SELECT ten_loai, gia, id_bienthe, ten_san_pham FROM view_chi_tiet_san_pham WHERE sku = %s", 
                (current_sku,)
            )
            current_item = cursor.fetchone()

            if not current_item:
                dispatcher.utter_message(text=f"Shop không tìm thấy thông tin cho mã SKU: {current_sku}.")
                return []

            # 3. Tìm sản phẩm tương đương dựa trên logic JOIN
            similar_items = find_similar_products(
                cursor, 
                current_item['ten_loai'], 
                current_item['gia'], 
                current_item['id_bienthe']
            )

            if not similar_items:
                dispatcher.utter_message(text=f"Dạ, mẫu **{current_item['ten_san_pham']}** hiện là mẫu độc nhất trong tầm giá này tại shop rồi ạ.")
                return []

            # 4. Hiển thị kết quả sống động
            msg = f"💡 Dựa trên mẫu **{current_item['ten_san_pham']}**, shop gợi ý bạn các lựa chọn tương đương này:"
            buttons = []

            for item in similar_items:
                price_fmt = "{:,.0f}".format(item['gia'])
                msg += f"\n\n🔹 **{item['ten_san_pham']}**\n💰 Giá: **{price_fmt} VNĐ**"
                
                # Sử dụng hàm create_button bạn đã sửa với intent ask_...
                buttons.append(create_button(
                    title=f"Xem chi tiết {item['sku']}",
                    intent="ask_get_product_price_specs",
                    entities_dict={"product_bienthe": item['sku']}
                ))

            # Thêm nút quay lại để khách dễ điều hướng
            buttons.append(create_button("🔙 Quay lại danh mục", "ask_browse_shop", {}))

            dispatcher.utter_message(text=msg, buttons=buttons)

        except Exception as e:
            print(f"Lỗi SearchSimilar: {e}")
            dispatcher.utter_message(text="🤖 Shop gặp chút trục trặc khi tìm sản phẩm tương tự, bạn thử lại sau nhé.")
        
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

        return []

