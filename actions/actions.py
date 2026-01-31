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
    Kết hợp SQL LIKE và Fuzzy Matching để tìm ID sản phẩm/biến thể.
    - type_input: 'product_name' hoặc 'sku'
    - data_input: giá trị chuỗi khách nhập
    - data_output: (id_sp, id_bienthe)
    """
    if not data_input:
        return None, type_input, None, "Dữ liệu đầu vào trống."

    raw_data = data_input
    search_term = unidecode(str(data_input)).lower().strip()
    
    try:
        # --- BƯỚC 1: TÌM KIẾM BẰNG SQL LIKE (Ưu tiên tốc độ và độ chính xác cao) ---
        if type_input == 'product_name':
            query = "SELECT id_sp, id_bienthe, ten_san_pham FROM view_chi_tiet_san_pham WHERE ten_san_pham LIKE %s"
            params = (f"%{data_input}%",)
        elif type_input == 'product_bienthe':
            query = "SELECT id_sp, id_bienthe, ten_san_pham FROM view_chi_tiet_san_pham WHERE sku LIKE %s"
            params = (f"%{data_input}%",)
        else:
            return raw_data, type_input, None, "Kiểu lọc không hợp lệ."

        cursor.execute(query, params)
        results = cursor.fetchall()

        # Nếu LIKE tìm thấy kết quả, lấy cái đầu tiên và trả về luôn
        if results:
            data_output = results[0]['id_sp'] if type_input == 'product_name' else results[0]['id_bienthe']
            return raw_data, type_input, data_output, None

        # --- BƯỚC 2: FUZZY MATCHING (Chạy khi LIKE thất bại - xử lý sai chính tả/viết tắt) ---
        # Lấy toàn bộ danh sách từ VIEW để làm tập dữ liệu so khớp
        cursor.execute("SELECT id_sp, id_bienthe, ten_san_pham, sku FROM view_chi_tiet_san_pham")
        all_data = cursor.fetchall()
        
        if not all_data:
            return raw_data, type_input, None, "Kho hàng hiện tại đang trống."

        # Chuẩn bị dữ liệu so khớp dựa trên type_input
        if type_input == 'product_name':
            choices = {unidecode(item['ten_san_pham']).lower(): item for item in all_data}
            # Thực hiện so khớp mờ
            best_match = process.extractOne(search_term, choices.keys(), scorer=fuzz.token_set_ratio)

            # Kiểm tra ngưỡng tin cậy (Score > 70/100)
            if best_match and best_match[1] >= 70:
                matched_item = choices[best_match[0]]
                data_output = matched_item['id_sp']
                return raw_data, type_input, data_output, None
        else: # sku
            choices = {unidecode(item['sku']).lower(): item for item in all_data}
            # Thực hiện so khớp mờ
            best_match = process.extractOne(search_term, choices.keys(), scorer=fuzz.token_set_ratio)

            # Kiểm tra ngưỡng tin cậy (Score > 70/100)
            if best_match and best_match[1] >= 70:
                matched_item = choices[best_match[0]]
                data_output = matched_item['id_bienthe']
                return raw_data, type_input, data_output, None
        
        # Nếu cả 2 cách đều thất bại
        return raw_data, type_input, None, f"Không tìm thấy sản phẩm nào khớp với '{data_input}'."

    except Exception as e:
        return raw_data, type_input, None, f"Lỗi xử lý: {str(e)}"

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
    Tìm kiếm thương hiệu bằng LIKE và Fuzzy, sau đó đếm số sản phẩm chính.
    Returns: id_th, ten_th, so_luong, list_sp, error
    """
    if not thuonghieu_input:
        return None, None, 0, [], "Dữ liệu đầu vào trống."

    search_term = unidecode(str(thuonghieu_input)).lower().strip()
    id_th, ten_th = None, None

    try:
        # --- BƯỚC 1: SQL LIKE (Tìm nhanh chính xác) ---
        query_like = "SELECT id_thuonghieu, ten FROM THUONGHIEU WHERE ten LIKE %s"
        cursor.execute(query_like, (f"%{thuonghieu_input}%",))
        result = cursor.fetchone()

        if result:
            id_th = result['id_thuonghieu']
            ten_th = result['ten']
        else:
            # --- BƯỚC 2: FUZZY MATCHING (Nếu LIKE thất bại) ---
            cursor.execute("SELECT id_thuonghieu, ten FROM THUONGHIEU")
            all_brands = cursor.fetchall()
            
            if all_brands:
                # Tạo dictionary để so khớp: {tên_không_dấu: item_gốc}
                choices = {unidecode(b['ten']).lower(): b for b in all_brands}
                best_match = process.extractOne(search_term, choices.keys(), scorer=fuzz.token_set_ratio)

                if best_match and best_match[1] >= 70:
                    matched_brand = choices[best_match[0]]
                    id_th = matched_brand['id_thuonghieu']
                    ten_th = matched_brand['ten']

        # --- BƯỚC 3: TRUY VẤN SẢN PHẨM NẾU TÌM THẤY THƯƠNG HIỆU ---
        if id_th:
            # Dùng DISTINCT id_sp để đếm số sản phẩm chính (không đếm trùng các biến thể SKU)
            query_sp = "SELECT DISTINCT id_sp, ten_san_pham FROM view_chi_tiet_san_pham WHERE id_thuonghieu = %s"
            cursor.execute(query_sp, (id_th,))
            list_results = cursor.fetchall()

            so_luong = len(list_results)
            list_sanpham = [item['ten_san_pham'] for item in list_results]

            return id_th, ten_th, so_luong, list_sanpham, None
        
        return None, None, 0, [], f"Không tìm thấy thương hiệu nào khớp với '{thuonghieu_input}'."

    except Exception as e:
        return None, None, 0, [], f"Lỗi hệ thống: {str(e)}"

def count_thuonghieu_by_type(cursor, loai_input):
    """
    Sử dụng thefuzz để tìm danh mục và trả về danh sách thương hiệu.
    """
    if not loai_input:
        return None, None, 0, [], "Dữ liệu đầu vào trống."

    # Chuẩn hóa đầu vào: bỏ dấu, viết thường, xóa khoảng trắng thừa
    search_term = unidecode(str(loai_input)).lower().strip()
    id_loai, ten_loai = None, None

    try:
        # --- BƯỚC 1: SQL LIKE ---
        query_like = "SELECT id_loai, ten_loai FROM DANHMUC WHERE ten_loai LIKE %s"
        cursor.execute(query_like, (f"%{loai_input}%",))
        result = cursor.fetchone()

        if result:
            id_loai = result['id_loai']
            ten_loai = result['ten_loai']
        else:
            # --- BƯỚC 2: THEFUZZ (Nếu LIKE không ra kết quả) ---
            cursor.execute("SELECT id_loai, ten_loai FROM DANHMUC")
            all_types = cursor.fetchall()
            
            if all_types:
                # Tạo dictionary so khớp: {tên_không_dấu: object_gốc}
                choices = {unidecode(t['ten_loai']).lower(): t for t in all_types}
                
                # Sử dụng process.extractOne của thefuzz
                # Scorer fuzz.token_set_ratio hoạt động rất tốt với chuỗi có thứ tự từ bị đảo lộn
                best_match = process.extractOne(search_term, choices.keys(), scorer=fuzz.token_set_ratio)

                # Kiểm tra ngưỡng tin cậy (trên 70%)
                if best_match and best_match[1] >= 70:
                    matched_key = best_match[0]
                    id_loai = choices[matched_key]['id_loai']
                    ten_loai = choices[matched_key]['ten_loai']

        # --- BƯỚC 3: LẤY THƯƠNG HIỆU TỪ VIEW NẾU TÌM THẤY LOẠI ---
        if id_loai:
            # Lấy các thương hiệu duy nhất thuộc danh mục này
            query_th = "SELECT DISTINCT ten_thuonghieu FROM view_chi_tiet_san_pham WHERE ten_loai = %s"
            cursor.execute(query_th, (ten_loai,))
            brand_results = cursor.fetchall()

            list_ten_th = [b['ten_thuonghieu'] for b in brand_results]
            so_luong_th = len(list_ten_th)

            return id_loai, ten_loai, so_luong_th, list_ten_th, None
        
        return None, None, 0, [], f"Tiếc quá, shop không tìm thấy loại sản phẩm nào tên là '{loai_input}' ạ."

    except Exception as e:
        return None, None, 0, [], f"Lỗi xử lý database: {str(e)}"

def search_products_complex(cursor, loai_name=None, hang_name=None, thuoctinh=None, giatri=None):
    """
    Tìm kiếm sản phẩm sử dụng get_id để chuẩn hóa ID và thefuzz để lọc thuộc tính.
    """
    id_loai = None
    id_hang = None
    
    # --- BƯỚC 1: CHUẨN HÓA ID BẰNG HÀM GET_ID ---
    if loai_name:
        _, id_loai, _, _ = get_id(cursor, 'loai', loai_name)
    
    if hang_name:
        _, id_hang, _, _ = get_id(cursor, 'hang', hang_name)

    # --- BƯỚC 2: TRUY VẤN SQL CƠ BẢN ---
    query = "SELECT * FROM view_chi_tiet_san_pham WHERE 1=1"
    params = []

    if id_loai:
        query += " AND id_loai = %s"
        params.append(id_loai)
    
    if id_hang:
        query += " AND id_thuonghieu = %s"
        params.append(id_hang)

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

# HÀM HELPER 2: Tạo Button an toàn (Fix lỗi payload)
def create_button(title, intent, entities_dict):
    return {
        "title": title,
        "payload": f"/{intent}{json.dumps(entities_dict, ensure_ascii=False)}"
    }

class ActionGetProductPriceSpecs(Action):
    def name(self) -> Text:
        return "action_get_product_price_specs"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        cursor = None
        connection = get_db_connection()
        if not connection:
            return []

        try:
            cursor = connection.cursor(dictionary=True)

            # 1. Chỉ lấy product_bienthe từ Entity hoặc Slot
            raw_bienthe = next(tracker.get_latest_entity_values("product_bienthe"), None)
            if not raw_bienthe:
                raw_bienthe = tracker.get_slot("product_bienthe")

            if not raw_bienthe:
                dispatcher.utter_message(text="Bạn vui lòng cung cấp mã sản phẩm (SKU) để shop kiểm tra nhé!")
                return []

            # 2. Gọi hàm tìm kiếm theo kiểu 'product_bienthe'
            # d_out lúc này trả về id_bienthe (giá trị đơn)
            _, t_in, d_out, error_msg = find_products_in_db(tracker, cursor, 'product_bienthe', raw_bienthe)
            
            if error_msg or not d_out:
                dispatcher.utter_message(text=f"Shop không tìm thấy mã '{raw_bienthe}'. Bạn kiểm tra lại giúp shop nhé!")
                return [SlotSet("product_bienthe", None)]

            # 3. Truy vấn chi tiết dựa trên id_bienthe (d_out)
            query = "SELECT * FROM view_chi_tiet_san_pham WHERE id_bienthe = %s"
            cursor.execute(query, (d_out,))
            res = cursor.fetchone()

            if not res:
                msg = (f"Xin lỗi, shop chưa có thông tin mô tả cho sản phẩm '{raw_bienthe}' ạ.\n\n"
                    f"Bạn có muốn xem qua những mẫu đang sẵn hàng tại shop không?")
                # Gợi ý khách xem các sản phẩm khác bằng nút bấm
                buttons = [
                    {"title": "📦 Xem danh sách sản phẩm", "payload": "/browse_shop"},
                    {"title": "🔍 Thử tìm tên khác", "payload": "/action_get_product_price_specs"},
                    {"title": "📞 Cần nhân viên gọi lại", "payload": "/out_of_scope"}
                ]
                dispatcher.utter_message(text=msg, buttons=buttons)
                return []
                

            # 4. Trình bày Giá + Thông số (Dạng bảng tin chi tiết)
            price = "{:,.0f}".format(res['gia'])
            
            msg = f"✅ **Thông tin: {res['ten_san_pham']}**\n"
            msg += f"🆔 Mã hiệu: `{res['sku']}`\n"
            msg += f"💰 Giá ưu đãi: **{price} VNĐ**\n"
            msg += "----------------------------\n"
            msg += "⚙️ **Cấu hình chi tiết:**\n"

            # Giải mã và lặp qua thông số
            if res.get('thongsokythuat'):
                try:
                    specs = json.loads(res['thongsokythuat'])
                    for key, value in specs.items():
                        # Làm đẹp tên thông số (Ví dụ: cpu_speed -> Cpu speed)
                        display_key = key.replace("_", " ").capitalize()
                        msg += f"📍 {display_key}: {value}\n"
                except:
                    msg += "📍 Thông số đang chờ cập nhật...\n"
            
            msg += "----------------------------\n"

            # Thêm nút bấm chốt đơn hoặc hỗ trợ khác
            buttons = [
                {"title": "📦 Xem danh sách sản phẩm", "payload": "/browse_shop"},
                {"title": "💳 Đặt mua ngay", "payload": "/out_of_scope"},
                {"title": "📞 Cần tư vấn thêm", "payload": "/out_of_scope"}
            ]

            dispatcher.utter_message(text=msg, buttons=buttons)

        except Exception as e:
            print(f"Lỗi Specs Only: {e}")
            dispatcher.utter_message(text="Có lỗi xảy ra, shop sẽ phản hồi lại ngay!")
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

        return [SlotSet("product_bienthe", raw_bienthe)]

class ActionGetProductDescription(Action):
    def name(self) -> Text:
        return "action_get_product_description"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        cursor = None
        connection = get_db_connection()
        if not connection:
            dispatcher.utter_message(text="⚠️ Lỗi kết nối database.")
            return []

        try:
            cursor = connection.cursor(dictionary=True)

            # 1. Lấy tên sản phẩm khách nhập từ Entity hoặc Slot
            raw_input = next(tracker.get_latest_entity_values("product_name"), None)
            if not raw_input:
                raw_input = tracker.get_slot("product_name")

            if not raw_input:
                dispatcher.utter_message(text="❓ Bạn muốn xem thông tin của sản phẩm nào ạ?")
                return []

            # 2. Bước 1: Tìm ID sản phẩm bằng hàm find_products_in_db
            # Hàm này trả về id_sp (giá trị đơn) vì ta truyền type_input='product_name'
            _, t_in, id_sp_found, error_msg = find_products_in_db(tracker, cursor, 'product_name', raw_input)

            if error_msg or not id_sp_found:
                error_msg = (f"Xin lỗi, shop chưa có thông tin mô tả cho sản phẩm '{raw_input}' ạ.\n\n"
                    f"Bạn có muốn xem qua những mẫu đang sẵn hàng tại shop không?")
                # Gợi ý khách xem các sản phẩm khác bằng nút bấm
                buttons = [
                    {"title": "📦 Xem danh sách sản phẩm", "payload": "/browse_shop"},
                    {"title": "🔍 Thử tìm tên khác", "payload": "/action_get_product_description"},
                    {"title": "📞 Cần nhân viên gọi lại", "payload": "/out_of_scope"}
                ]
                dispatcher.utter_message(text=error_msg, buttons=buttons)
                return [SlotSet("product_name", None)]

            # 3. Bước 2: Lấy chi tiết các biến thể từ VIEW bằng hàm get_product_view_by_id
            results, view_error = get_product_view_by_id(cursor, id_sp_found)

            if view_error or not results:
                dispatcher.utter_message(text="Dữ liệu mô tả sản phẩm đang được cập nhật.")
                return []

            # 4. Trích xuất thông tin chung (Lấy từ dòng đầu tiên của kết quả)
            first_item = results[0]
            product_name = first_item['ten_san_pham']
            product_type = first_item['ten_loai']
            proudct_thuonghieu = first_item['ten_thuonghieu']
            # Giả sử cột mô tả trong VIEW của bạn tên là 'mo_ta'
            description = first_item.get('mo_ta')

            # 5. Xây dựng tin nhắn phản hồi
            msg = f"📖 Sản phẩm **{product_type}** **{product_name}** của hãng **{proudct_thuonghieu}**\n\n"
            msg += f"là {description}\n\n"
            msg += "👇 **Chọn phiên bản bên dưới để xem giá và cấu hình chi tiết:**"

            # 6. Tạo danh sách nút bấm (Nút SKU trỏ đến action_get_product_price_specs)
            buttons = []
            for item in results:
                v_sku = item['sku']
                # Payload này gửi entity product_bienthe cho action tiếp theo
                payload = f'/ask_price_specs{{"product_bienthe": "{v_sku}"}}'
                buttons.append({
                    "title": f"Mã {v_sku}",
                    "payload": payload
                })

            # Gửi tin nhắn kèm tối đa 10 nút bấm (Giới hạn của hầu hết các chat platform)
            dispatcher.utter_message(text=msg, buttons=buttons[:10])

            # Lưu lại tên chuẩn vào Slot
            return [SlotSet("product_name", product_name)]

        except Exception as e:
            print(f"Lỗi ActionGetDescription: {e}")
            dispatcher.utter_message(text="Xin lỗi, tôi gặp chút trục trặc khi lấy dữ liệu.")
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
            dispatcher.utter_message(text="⚠️ Lỗi kết nối database.")
            return []

        try:
            cursor = connection.cursor(dictionary=True)

            # 1. Lấy thực thể thương hiệu từ người dùng
            brand_input = next(tracker.get_latest_entity_values("product_thuonghieu"), None)
            
            if not brand_input:
                # Nếu không có thực thể, thử lấy từ slot (trong trường hợp đã lưu trước đó)
                brand_input = tracker.get_slot("product_thuonghieu")

            if not brand_input:
                dispatcher.utter_message(text="❓ Bạn muốn xem sản phẩm của hãng nào ạ?")
                return []

            # 2. Gọi hàm count_product_by_thuonghieu (Hàm bạn đã viết ở bước trước)
            # Trả về: id_th, ten_th, so_luong, list_sanpham, text_error
            id_th, ten_th, count, products, err = count_product_by_thuonghieu(cursor, brand_input)

            # 3. Xử lý lỗi hoặc không tìm thấy
            if err:
                error_msg = (f"Dạ, {err}\n\n"
                f"Bạn có muốn xem qua những mẫu đang sẵn hàng tại shop không?")
                # Gợi ý khách xem các sản phẩm khác bằng nút bấm
                buttons = [
                    {"title": "📦 Xem danh sách sản phẩm", "payload": "/browse_shop"},
                    {"title": "🔍 Thử tìm tên khác", "payload": "/action_show_product_by_brand"},
                    {"title": "📞 Cần nhân viên gọi lại", "payload": "/out_of_scope"}
                ]
                dispatcher.utter_message(text=error_msg, buttons=buttons)
                return [SlotSet("product_thuonghieu", None)]

            if count == 0:
                dispatcher.utter_message(text=f"Hiện tại mẫu của hãng **{ten_th}** đang hết hàng hoặc chưa được cập nhật ạ.")
                return []

            # 4. Tạo tin nhắn phản hồi
            msg = f"🏢 Hãng **{ten_th}** đang có **{count}** dòng máy tại shop.\n\n"
            msg += "Dưới đây là danh sách sản phẩm, bạn nhấn vào để xem chi tiết mô tả nhé:"

            # 5. Tạo danh sách nút bấm động
            buttons = []
            for p_name in products:
                # Payload này sẽ kích hoạt action_get_product_description
                # Chúng ta truyền tên sản phẩm chuẩn vào entity product_name
                payload = f'/action_get_product_description{{"product_name": "{p_name}"}}'
                buttons.append({
                    "title": f"🔍 {p_name}",
                    "payload": payload
                })

            # Hiển thị tối đa 10 sản phẩm (giới hạn nút bấm thông thường)
            dispatcher.utter_message(text=msg, buttons=buttons[:10])

            # 6. Cập nhật Slot để Bot ghi nhớ ngữ cảnh hãng đang nói tới
            return [SlotSet("product_thuonghieu", ten_th)]

        except Exception as e:
            print(f"Lỗi ActionShowProductByBrand: {e}")
            dispatcher.utter_message(text="Hệ thống bận, vui lòng thử lại sau.")
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
            return []

        try:
            cursor = connection.cursor(dictionary=True)

            # Lấy loại sản phẩm từ thực thể
            type_input = next(tracker.get_latest_entity_values("loai_san_pham"), None)
            if not type_input:
                type_input = tracker.get_slot("loai_san_pham")

            if not type_input:
                dispatcher.utter_message(text="Bạn muốn xem thương hiệu của dòng sản phẩm nào? (Ví dụ: Bàn phím, Chuột...)")
                return []

            # Gọi hàm count bằng thefuzz
            id_loai, ten_loai, count, brands, err = count_thuonghieu_by_type(cursor, type_input)

            if err:
                error_msg = (f"Dạ, {err}\n\n"
                f"Bạn có muốn xem qua những mẫu đang sẵn hàng tại shop không?")
                # Gợi ý khách xem các sản phẩm khác bằng nút bấm
                buttons = [
                    {"title": "📦 Xem danh sách sản phẩm", "payload": "/browse_shop"},
                    {"title": "🔍 Thử tìm tên khác", "payload": "/action_show_brand_by_type"},
                    {"title": "📞 Cần nhân viên gọi lại", "payload": "/out_of_scope"}
                ]
                dispatcher.utter_message(text=error_msg, buttons=buttons)
                return []

            if count == 0:
                dispatcher.utter_message(text=f"Hiện tại shop chưa có hãng nào cho mục **{ten_loai}**.")
                return []

            # Phản hồi khách hàng
            msg = f"📦 Với dòng **{ten_loai}**, shop đang có sản phẩm từ **{count}** hãng sau đây:"
            
            buttons = []
            for b_name in brands:
                # Khi bấm vào nút này, Rasa sẽ kích hoạt action_show_product_by_brand
                payload = f'/action_show_product_by_brand{{"product_thuonghieu": "{b_name}"}}'
                buttons.append({
                    "title": f"🏢 {b_name}",
                    "payload": payload
                })

            dispatcher.utter_message(text=msg, buttons=buttons[:10])

            # Cập nhật slot để ghi nhớ ngữ cảnh
            return [SlotSet("loai_san_pham", ten_loai)]

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
            dispatcher.utter_message(text="⚠️ Lỗi kết nối hệ thống dữ liệu.")
            return []

        try:
            cursor = connection.cursor(dictionary=True)

            # 1. Lấy tổng số lượng biến thể sản phẩm (Tổng kho)
            # Truy vấn từ bảng BIENTHESP hoặc VIEW
            cursor.execute("SELECT COUNT(*) as total FROM BIENTHESP")
            total_count = cursor.fetchone()['total']

            # 2. Lấy danh sách các loại sản phẩm từ bảng DANHMUC
            cursor.execute("SELECT id_loai, ten_loai FROM DANHMUC")
            categories = cursor.fetchall()
            total_types = len(categories)

            if not categories:
                dispatcher.utter_message(text="Hiện tại shop đang cập nhật danh mục hàng hóa, bạn quay lại sau nhé!")
                return []

            # 3. Xây dựng thông điệp chào mừng
            msg = (f"🌟 **Gemini Shop** chào bạn! Hiện shop đang có sẵn **{total_count}** mã hàng "
                   f"thuộc **{total_types}** nhóm sản phẩm khác nhau.\n\n"
                   f"Bạn muốn khám phá danh mục nào dưới đây?")

            # 4. Tạo các nút bấm trỏ đến ActionShowBrandByType
            buttons = []
            for cat in categories:
                cat_name = cat['ten_loai']
                
                # Payload này sẽ kích hoạt ActionShowBrandByType
                # Đảm bảo entity 'loai_san_pham' khớp với khai báo trong nlu.yml
                payload = f'/action_show_brand_by_type{{"loai_san_pham": "{cat_name}"}}'
                
                buttons.append({
                    "title": f"📦 {cat_name}",
                    "payload": payload
                })

            # Gửi thông điệp kèm nút bấm (giới hạn hiển thị nếu quá nhiều category)
            dispatcher.utter_message(text=msg, buttons=buttons[:10])

        except Exception as err:
            print(f"Lỗi BrowseShop: {err}")
            dispatcher.utter_message(text="Rất xin lỗi, shop không thể lấy danh mục lúc này.")
        
        finally:
            if cursor: cursor.close()
            if connection and connection.is_connected():
                connection.close()

        return []

class ActionSearchProductBySpecs(Action):
    def name(self) -> str:
        return "action_search_product_by_specs"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict) -> list:
        
        connection = get_db_connection()
        if not connection: return []
        
        cursor = connection.cursor(dictionary=True)

        # Lấy các thực thể từ hội thoại
        loai = next(tracker.get_latest_entity_values("loai_san_pham"), None)
        hang = next(tracker.get_latest_entity_values("product_thuonghieu"), None)
        attr_name = next(tracker.get_latest_entity_values("attribute_name"), None)
        attr_value = next(tracker.get_latest_entity_values("attribute_value"), None)

        # Tìm kiếm
        results = search_products_complex(cursor, loai, hang, attr_name, attr_value)

        if not results:
            # Gợi ý "Tương tự" nếu không tìm thấy cấu hình cụ thể
            if attr_name or attr_value:
                results = search_products_complex(cursor, loai, hang)
                if results:
                    dispatcher.utter_message(text="👉 Shop không có mẫu đúng yêu cầu đó, mời bạn xem các mẫu cùng loại:")
            
            if not results:
                dispatcher.utter_message(text="Dạ, shop hiện chưa có sản phẩm nào phù hợp với yêu cầu này.")
                return []

        # Hiển thị kết quả
        msg = "🔍 Danh sách sản phẩm phù hợp:"
        buttons = []
        for item in results[:5]:
            msg += f"\n\n✨ **{item['ten_san_pham']}**\n💰 Giá: {item['gia']:,} VNĐ"
            buttons.append({
                "title": f"Xem {item['sku']}",
                "payload": f'/action_get_product_price_specs{{"product_bienthe": "{item["sku"]}"}}'
            })

        dispatcher.utter_message(text=msg, buttons=buttons)
        
        cursor.close()
        connection.close()
        return []

