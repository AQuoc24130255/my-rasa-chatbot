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

# HÀM HELPER 2: Tạo Button an toàn (Fix lỗi payload)
def create_button(title, intent, entities_dict):
    return {
        "title": title,
        "payload": f"/{intent}{json.dumps(entities_dict, ensure_ascii=False)}"
    }

class ActionGetProductPrice(Action):
    def name(self) -> Text:
        return "action_get_product_price"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        cursor = None
        connection = get_db_connection()
        if not connection:
            dispatcher.utter_message(text="Lỗi kết nối database.")
            return []

        events = []

        try:
            cursor = connection.cursor(dictionary=True)

            # 1. Gọi hàm tìm kiếm mới (trả về 4 giá trị)
            raw_name = next(tracker.get_latest_entity_values("product_name"), None)
            raw_bienthe = next(tracker.get_latest_entity_values("product_bienthe"), None)

            if not raw_name and not raw_bienthe:
                raw_name = tracker.get_slot("product_name")

            d_out = None
            t_in = None
            final_raw = None
            error_msg = None

            if raw_name:
                raw_name, t_in, d_out, error_msg = find_products_in_db(tracker, cursor, 'product_name', raw_name)
            elif raw_bienthe:
                raw_name, t_in, d_out, error_msg = find_products_in_db(tracker, cursor, 'product_bienthe', raw_bienthe)
            
            # 2. Xử lý khi KHÔNG tìm thấy sản phẩm
            if error_msg or not d_out:
                msg = error_msg if error_msg else f"Tiếc quá, hiện tại shop chưa có thông tin cho '{raw_name}' ạ."
                buttons = [
                    {"title": "📦 Xem danh mục", "payload": "/browse_shop"},
                    {"title": "🔍 Tìm sản phẩm khác", "payload": "/ask_price"},
                    {"title": "📞 Cần nhân viên gọi lại", "payload": "/out_of_scope"}
                ]
                dispatcher.utter_message(text=msg, buttons=buttons)
                events.append(SlotSet("product_name", None))
                return events

            # 3. Lấy toàn bộ biến thể từ VIEW dựa trên d_out tìm được
            if t_in == 'product_name':
                query_view = "SELECT * FROM view_chi_tiet_san_pham WHERE id_sp = %s"
            elif t_in == 'product_bienthe':
                query_view = "SELECT * FROM view_chi_tiet_san_pham WHERE id_bienthe = %s"

            cursor.execute(query_view, (d_out,))
            variants = cursor.fetchall()


            if not variants:
                dispatcher.utter_message(text="Dữ liệu chi tiết sản phẩm đang được cập nhật, bạn quay lại sau nhé!")
                return events

            # 4. Hiển thị thông tin
            first_var = variants[0]
            product_name = first_var['ten_san_pham']
            proudct_thuonghieu = first_var['ten_thuonghieu']

            if len(variants) == 1:
                # Trường hợp chỉ có 1 biến thể duy nhất
                price = "{:,.0f}".format(first_var['gia'])
                msg = (f"Dạ, mẫu **{product_name}**, mã **{first_var['sku']}** của hãng {proudct_thuonghieu} "
                       f"hiện có giá là **{price} VNĐ** ạ.")
                # Thêm nút bấm xem cấu hình cho tiện
                buttons = [{"title": "⚙️ Xem thông số", "payload": f"/ask_specs"}]
                dispatcher.utter_message(text=msg, buttons=buttons)
            else:
                # Trường hợp có nhiều biến thể (ví dụ nhiều màu, nhiều dung lượng)
                msg = f"Dạ, mẫu **{product_name}** của hãng {proudct_thuonghieu} shop đang có các phiên bản sau:\n\n"
                buttons = []
                
                for var in variants:
                    v_price = "{:,.0f}".format(var['gia'])
                    v_sku = var['sku']
                    msg += f"🔹 Mã `{v_sku}`: **{v_price} VNĐ**\n"
                    
                    # SỬA LỖI PAYLOAD: Sử dụng dấu nháy đơn bao ngoài dấu nháy kép cho JSON
                    payload = f'/ask_specs{{"product_bienthe": "{v_sku}"}}'
                    buttons.append({
                        "title": f"Cấu hình {v_sku}",
                        "payload": payload
                    })
                
                msg += "\nBạn quan tâm đến phiên bản nào trong số này ạ?"
                dispatcher.utter_message(text=msg, buttons=buttons)

            # Lưu tên sản phẩm chuẩn vào slot
            events.append(SlotSet("product_name", product_name))

        except Exception as err:
            print(f"Lỗi thực thi: {err}")
            dispatcher.utter_message(text="Hệ thống đang bận, bạn vui lòng thử lại sau nhé!")
        
        finally:
            if cursor: cursor.close()
            if connection and connection.is_connected(): connection.close()

        return events

class ActionGetProductSpecs(Action):
    def name(self) -> Text:
        return "action_get_product_specs"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            
        cursor = None
        connection = get_db_connection()
        if not connection:
            return []

        try:
            cursor = connection.cursor(dictionary=True)

            # 1. Lấy Entity từ tracker (Ưu tiên SKU nếu khách nhấn từ nút bấm báo giá)
            raw_name = next(tracker.get_latest_entity_values("product_name"), None)
            raw_bienthe = next(tracker.get_latest_entity_values("product_bienthe"), None)

            if not raw_name and not raw_bienthe:
                raw_name = tracker.get_slot("product_name")

            d_out = None
            t_in = None
            error_msg = None

            # 2. Logic tìm kiếm tương tự ActionGetProductPrice
            if raw_bienthe:
                # Nếu có SKU, tìm chính xác cấu hình của biến thể đó
                _, t_in, d_out, error_msg = find_products_in_db(tracker, cursor, 'product_bienthe', raw_bienthe)
            elif raw_name:
                # Nếu khách chỉ nói tên chung chung, tìm theo tên sản phẩm
                _, t_in, d_out, error_msg = find_products_in_db(tracker, cursor, 'product_name', raw_name)
            else:
                dispatcher.utter_message(text="Bạn muốn xem cấu hình của sản phẩm nào ạ?")
                return []

            # Kiểm tra kết quả trả về
            if error_msg or not d_out:
                msg = error_msg if error_msg else f"Tiếc quá, shop chưa có thông số cho sản phẩm này."
                dispatcher.utter_message(text=msg)
                return []

            # 3. Truy vấn lấy thông số từ VIEW
            # d_out lúc này đã là ID đơn (id_sp hoặc id_bienthe)
            if t_in == 'product_name':
                # Nếu tìm theo tên, lấy biến thể đầu tiên của sản phẩm đó để hiện cấu hình mẫu
                query = "SELECT * FROM view_chi_tiet_san_pham WHERE id_sp = %s LIMIT 1"
            else:
                # Nếu tìm theo biến thể, lấy đúng cấu hình của biến thể đó
                query = "SELECT * FROM view_chi_tiet_san_pham WHERE id_bienthe = %s"

            cursor.execute(query, (d_out,))
            result = cursor.fetchone()

            if result and result.get('thongsokythuat'):
                # Giải mã JSON
                try:
                    specs = json.loads(result['thongsokythuat'])
                except Exception:
                    specs = {}

                msg = f"⚙️ **Thông số: {result['ten_san_pham']}**\n"
                msg += f"🔹 SKU: `{result['sku']}` | Loại: {result['ten_loai']}\n"
                msg += "----------------------------\n"

                if specs:
                    for key, value in specs.items():
                        display_key = key.replace("_", " ").capitalize()
                        msg += f"📍 {display_key}: {value}\n"
                else:
                    msg += "Dữ liệu cấu hình đang được cập nhật..."

                dispatcher.utter_message(text=msg)
            else:
                product_label = result['ten_san_pham'] if result else "này"
                dispatcher.utter_message(text=f"Dạ, mẫu {product_label} hiện chưa có bảng thông số chi tiết ạ.")

        except Exception as e:
            print(f"Lỗi ActionGetProductSpecs: {e}")
            dispatcher.utter_message(text="Có lỗi khi hiển thị cấu hình, bạn đợi shop chút nhé!")
        
        finally:
            if cursor: cursor.close()
            if connection and connection.is_connected(): connection.close()

        return []

class ActionGetProductDescription(Action):
    def name(self) -> Text:
        # Tên này phải trùng với khai báo trong domain.yml
        return "action_get_product_description"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        cursor = None
        # Kết nối Database (Dùng IP 127.0.0.1 để tránh lỗi socket)
        connection = get_db_connection()
        if not connection:
            dispatcher.utter_message(text="Lỗi kết nối database.")
            return []

        events = []

        try:
            cursor = connection.cursor(dictionary=True)

            raw_product_name, results = find_products_in_db(tracker, cursor)

            if not results:
                if not raw_product_name:
                    dispatcher.utter_message(text="Bạn muốn hỏi thông tin của sản phẩm nào ạ?")
                else:
                    msg = (f"Xin lỗi, shop chưa có thông tin mô tả cho sản phẩm '{raw_product_name}' ạ.\n\n"
                        f"Bạn có muốn xem qua những mẫu đang sẵn hàng tại shop không?")
                    # Gợi ý khách xem các sản phẩm khác bằng nút bấm
                    buttons = [
                        {"title": "📦 Xem danh sách sản phẩm", "payload": "/browse_shop"},
                        {"title": "🔍 Thử tìm tên khác", "payload": "/ask_price"},
                        {"title": "📞 Cần nhân viên gọi lại", "payload": "/out_of_scope"}
                    ]
                    dispatcher.utter_message(text=msg, buttons=buttons)
                events.append(SlotSet("product_name", None))
            elif len(results) == 1:
                item = results[0]
                name = item['name']
                desc = item['description']
                dispatcher.utter_message(text=f"Thông tin chi tiết về {name}: {desc}")
                # Lưu tên sản phẩm chuẩn vào slot để lần sau khách hỏi "cấu hình nó" thì chính xác hơn
                events.append(SlotSet("product_name", item['name']))
            else:
                best_match = results[0]
                short_desc = (best_match['description'][:150] + '...') if len(best_match['description']) > 150 else best_match['description']
                names = ", ".join([r['name'] for r in results[1:]])

                msg = (f"Dạ, dòng '{raw_product_name}' shop có khá nhiều mẫu.\n\n"
                        f"🌟 **Nổi bật nhất** là {best_match['name']} với thông tin là **{short_desc}**.\n\n"
                        f"Ngoài ra, shop còn có: {names}. Bạn quan tâm mẫu nào trong số này ạ?")
                    
                dispatcher.utter_message(text=msg)
                events.append(SlotSet("product_name", best_match['name']))

        except mysql.connector.Error as err:
            print(f"Lỗi thực thi: {err}")
            dispatcher.utter_message(text="Hệ thống đang gặp lỗi kết nối dữ liệu.")
        
        finally:
            # --- Đóng kết nối an toàn ---
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

        return events

class ActionGetProductType(Action):
    def name(self) -> Text:
        return "action_get_product_type"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        cursor = None
        connection = get_db_connection()
        
        if not connection:
            dispatcher.utter_message(text="Lỗi kết nối database.")
            return []

        events = []

        try:
            cursor = connection.cursor(dictionary=True)
            # Sử dụng hàm helper chung để tìm kiếm sản phẩm
            raw_product_name, results = find_products_in_db(tracker, cursor)

            # TRƯỜNG HỢP 1: Không tìm thấy sản phẩm
            if not results:
                if not raw_product_name:
                    dispatcher.utter_message(text="Bạn muốn kiểm tra loại của sản phẩm nào ạ?")
                else:
                    msg = (f"Tiếc quá, shop chưa có thông tin phân loại cho '{raw_product_name}' ạ.\n\n"
                        f"Bạn có muốn xem qua những mẫu đang sẵn hàng tại shop không?")
                    buttons = [
                        {"title": "📦 Xem danh sách sản phẩm", "payload": "/browse_shop"},
		                {"title": "🔍 Thử tìm tên khác", "payload": "/ask_price"},
		                {"title": "📞 Cần nhân viên gọi lại", "payload": "/out_of_scope"}
	                ]
                    dispatcher.utter_message(text=msg, buttons=buttons)
                return [SlotSet("product_name", None)]
            # TRƯỜNG HỢP 2: Tìm thấy chính xác 1 sản phẩm
            elif len(results) == 1:
                item = results[0]
                name = item['name']
                p_type = item['type'] # Lấy trường 'type' từ DB
                
                dispatcher.utter_message(
                    text=f"Dạ, sản phẩm **{name}** thuộc dòng **{p_type}** của shop mình ạ."
                )
                events.append(SlotSet("product_name", name))
            # TRƯỜNG HỢP 3: Tìm thấy nhiều sản phẩm tương tự
            else:
                best_match = results[0]
                p_type = best_match['type']
                others = ", ".join([r['name'] for r in results[1:4]]) # Lấy thêm tối đa 3 mẫu khác

                msg = (f"Dạ, mẫu '{best_match['name']}' mà bạn quan tâm thuộc dòng **{p_type}**.\n\n"
                       f"Trong dòng này shop còn có: {others}. Bạn có muốn xem chi tiết mẫu nào không?")
                
                dispatcher.utter_message(text=msg)
                events.append(SlotSet("product_name", best_match['name']))

        except mysql.connector.Error as err:
            print(f"Lỗi thực thi: {err}")
            dispatcher.utter_message(text="Hệ thống đang gặp lỗi kết nối dữ liệu.")
            
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

        return events

class ActionCountProductByType(Action):
    def name(self) -> Text:
        return "action_count_product_by_type"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        cursor = None
        # 1. Lấy thực thể 'product_type' từ tin nhắn khách (ví dụ: "màn hình", "laptop")
        product_type = next(tracker.get_latest_entity_values("product_type"), None)
        if not product_type:
            product_type = tracker.get_slot("product_type")

        if not product_type:
            dispatcher.utter_message(text="Bạn muốn đếm loại sản phẩm nào ạ? (Ví dụ: màn hình, laptop...)")
            return []

        connection = get_db_connection()
        if not connection:
            dispatcher.utter_message(text="Lỗi kết nối database.")
            return []
        cursor = connection.cursor(dictionary=True)

        try:
            # 2. Lấy danh sách các 'type' duy nhất đang có trong Database
            cursor.execute("SELECT DISTINCT type FROM products")
            list_types = [row['type'] for row in cursor.fetchall()]

            if not list_types:
                dispatcher.utter_message(text="Hiện tại trong kho chưa có sản phẩm nào cả.")
                return []

            # 3. Dùng thefuzz để tìm loại khớp nhất với yêu cầu của khách
            # Ví dụ: Khách gõ "màn hình" -> Match với "Monitor" trong DB (nếu bạn đặt tên tiếng Anh)
            best_match = process.extractOne(product_type, list_types)

            if best_match and best_match[1] > 60:
                matched_type = best_match[0]

                # 4. Truy vấn đếm số lượng theo loại đã khớp
                query = "SELECT COUNT(*) as total FROM products WHERE type = %s"
                cursor.execute(query, (matched_type,))
                result = cursor.fetchone()
                count = result['total']

                if count > 0:
                    dispatcher.utter_message(
                        text=f"Dạ, hiện tại shop đang có {count} mẫu sản phẩm thuộc dòng **{matched_type}** ạ!"
                    )
                    # Gợi ý thêm nút bấm để khách xem danh sách
                    buttons = [
                        {"title": f"Xem các mẫu {matched_type}", "payload": f"/show_products_by_type{{\"product_type\":\"{matched_type}\"}}"}
                    ]
                    dispatcher.utter_message(buttons=buttons)
                else:
                    dispatcher.utter_message(text=f"Dòng {matched_type} hiện đang hết hàng rồi ạ.")
            else:
                dispatcher.utter_message(text=f"Shop hiện chưa có dòng sản phẩm nào tên là '{product_type}' ạ.")

        except Exception as e:
            print(f"Lỗi thực thi: {err}")
            dispatcher.utter_message(text=f"Có lỗi xảy ra khi truy xuất dữ liệu: {str(e)}")
        finally:
            # --- Đóng kết nối an toàn ---
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

        return []

class ActionShowProductsByType(Action):
    def name(self) -> Text:
        return "action_show_products_by_type"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        cursor = None
        # 1. Lấy loại sản phẩm khách yêu cầu
        product_type = next(tracker.get_latest_entity_values("product_type"), None)
        if not product_type:
            product_type = tracker.get_slot("product_type")

        if not product_type:
            dispatcher.utter_message(text="Bạn muốn xem loại sản phẩm nào ạ? (Ví dụ: Laptop, Màn hình...)")
            return []

        connection = get_db_connection()
        if not connection:
            dispatcher.utter_message(text="Lỗi kết nối database.")
            return []
        cursor = connection.cursor(dictionary=True)

        try:
            # 2. Lấy danh sách các loại thực tế trong DB để so khớp mờ (Fuzzy Match)
            cursor.execute("SELECT DISTINCT type FROM products")
            list_types = [row['type'] for row in cursor.fetchall()]
            
            best_match = process.extractOne(product_type, list_types)

            if best_match and best_match[1] > 60:
                matched_type = best_match[0]

                # 3. Truy vấn danh sách sản phẩm thuộc loại đó
                query = "SELECT name, price FROM products WHERE type = %s LIMIT 5"
                cursor.execute(query, (matched_type,))
                products = cursor.fetchall()

                if products:
                    dispatcher.utter_message(text=f"Đây là các mẫu **{matched_type}** mới nhất tại shop:")
                    
                    buttons = []
                    for p in products:
                        price_fmt = "{:,.0f}".format(p['price'])
                        # Tạo nút bấm: hiển thị Tên - Giá, khi nhấn sẽ gửi payload tìm sản phẩm đó
                        buttons.append({
                            "title": f"{p['name']} ({price_fmt}đ)",
                            "payload": f"/ask_description{{\"product_name\":\"{p['name']}\"}}"
                        })
                    
                    dispatcher.utter_message(buttons=buttons)
                else:
                    dispatcher.utter_message(text=f"Dòng {matched_type} hiện đang hết hàng rồi ạ.")
            else:
                dispatcher.utter_message(text=f"Rất tiếc, shop chưa có loại sản phẩm '{product_type}' này.")

        except Exception as e:
            print(f"Lỗi thực thi: {err}")
            dispatcher.utter_message(text=f"Lỗi hệ thống: {str(e)}")
        finally:
            # --- Đóng kết nối an toàn ---
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

        return []

class ActionBrowseShop(Action):
    def name(self) -> Text:
        return "action_browse_shop"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cursor = None
        connection = get_db_connection()
        if not connection:
            dispatcher.utter_message(text="Lỗi kết nối hệ thống.")
            return []

        try:
            cursor = connection.cursor(dictionary=True)

            # 1. Lấy tổng số lượng sản phẩm
            cursor.execute("SELECT COUNT(*) as total FROM products")
            total_count = cursor.fetchone()['total']

            # 2. Lấy danh sách các loại sản phẩm duy nhất (Categories)
            cursor.execute("SELECT DISTINCT type FROM products")
            categories = cursor.fetchall()

            # 3. Lấy tổng số lượng loại sản phẩm
            types = [row['type'] for row in categories if row['type']]
            total_types = len(types)

            if not categories:
                dispatcher.utter_message(text="Hiện tại shop đang cập nhật hàng mới, bạn quay lại sau nhé!")
                return []

            # 3. Xây dựng thông điệp
            msg = (f"🌟 **Gemini Shop** đang có sẵn **{total_count}** sản phẩm bao gồm **{total_types}** loại sản phẩm!\n"
                   f"Dưới đây là các danh mục bạn có thể khám phá:")

            # 4. Tạo các nút bấm dựa trên category (Dùng helper json.dumps để fix lỗi payload)
            buttons = []
            for cat in categories:
                category_name = cat['type']
                # Payload an toàn cho Rasa
                payload = f'/show_products_by_type{{"product_type": "{category_name}"}}'
                
                buttons.append({
                    "title": f"📦 {category_name.capitalize()}",
                    "payload": payload
                })

            dispatcher.utter_message(text=msg, buttons=buttons)

        except mysql.connector.Error as err:
            print(f"Lỗi thực thi: {err}")
            dispatcher.utter_message(text="Rất xin lỗi, hệ thống dữ liệu của shop đang gặp chút trục trặc. Bạn thử lại sau nhé!")
        
        finally:
            # --- Đóng kết nối an toàn ---
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

        return []
