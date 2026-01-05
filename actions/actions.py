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
def find_products_in_db(tracker, cursor, entity_name="product_name"):
    # 1. Lấy từ khóa từ Entity hoặc Slot
    raw_name = next(tracker.get_latest_entity_values(entity_name), None)
    if not raw_name:
        raw_name = tracker.get_slot(entity_name)
    
    if not raw_name:
        return None, None

    search_term = unidecode(raw_name).lower()
    keywords = re.findall(r'\b\w+\b', search_term)
    if not keywords:
        return raw_name, []

    # 2. CHIẾN THUẬT 1: SQL LIKE
    query = "SELECT * FROM products WHERE "
    conditions = [f"search_name LIKE %s"] * len(keywords[:4])
    params = [f"%{word}%" for word in keywords[:4]]
    
    query += " AND ".join(conditions)
    query += " ORDER BY LENGTH(name) ASC LIMIT 5"

    cursor.execute(query, tuple(params))
    results = cursor.fetchall()

    # 3. CHIẾN THUẬT 2: FUZZY MATCHING (Nếu LIKE thất bại)
    if not results:
        cursor.execute("SELECT * FROM products")
        all_prods = cursor.fetchall()
        if all_prods:
            choices = {p['search_name']: p for p in all_prods}
            match = process.extractOne(search_term, choices.keys(), scorer=fuzz.token_set_ratio)
            if match and match[1] > 70:
                results = [choices[match[0]]]

    return raw_name, results

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
        # Kết nối Database (Dùng IP 127.0.0.1 để tránh lỗi socket)
        connection = get_db_connection()
        if not connection:
            dispatcher.utter_message(text="Lỗi kết nối database.")
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)

            raw_product_name, results = find_products_in_db(tracker, cursor)

            events = []
            
            if not results:
                if not raw_product_name:
                    dispatcher.utter_message(text="Bạn muốn hỏi giá sản phẩm nào ạ?")
                else:
                    msg = (f"Tiếc quá, hiện tại shop chưa có thông tin giá cho '{raw_product_name}' ạ.\n\n"
                        f"Bạn có muốn xem qua những mẫu đang sẵn hàng tại shop không?")
                    # Gợi ý khách xem các sản phẩm khác bằng nút bấm
                    buttons = [
                        {"title": "📦 Xem danh sách sản phẩm", "payload": "/browse_shop"},
                        {"title": "🔍 Thử tìm tên khác", "payload": "/ask_price"},
                        {"title": "📞 Cần nhân viên gọi lại", "payload": "/out_of_scope"}
                    ]
                    dispatcher.utter_message(text=msg, buttons=buttons)
                events.append(SlotSet("product_name", None))
            
            if len(results) == 1:
                item = results[0]
                name = item['name']
                price = "{:,.0f}".format(item['price']) # Định dạng 150,000
                dispatcher.utter_message(text=f"Dạ, sản phẩm {name} hiện có giá là {price} VNĐ ạ.")
                # Lưu tên sản phẩm chuẩn vào slot để lần sau khách hỏi "cấu hình nó" thì chính xác hơn
                events.append(SlotSet("product_name", item['name']))
            elif len(results) > 1:
                best_match = results[0]
                names = ", ".join([r['name'] for r in results[1:]])

                price_suggest = "{:,.0f}".format(best_match['price'])

                msg = (f"Dạ, dòng '{raw_product_name}' shop có khá nhiều mẫu.\n\n"
                    f"🌟 **Nổi bật nhất** là {best_match['name']} với giá khoảng **{price_suggest} VNĐ**.\n\n"
                    f"Ngoài ra, shop còn có: {names}. Bạn quan tâm mẫu nào trong số này ạ?")
                    
                dispatcher.utter_message(text=msg)
                events.append(SlotSet("product_name", best_match['name']))

        except mysql.connector.Error as err:
            dispatcher.utter_message(text="Rất xin lỗi, hệ thống dữ liệu của shop đang gặp chút trục trặc. Bạn thử lại sau nhé!")
        
        finally:
            # --- Đóng kết nối an toàn ---
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

        return events

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
        try:
            cursor = connection.cursor(dictionary=True)

            raw_product_name, results = find_products_in_db(tracker, cursor)

            events = []
            
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
            
            if len(results) == 1:
                item = results[0]
                name = item['name']
                desc = item['description']
                dispatcher.utter_message(text=f"Thông tin chi tiết về {name}: {desc}")
                # Lưu tên sản phẩm chuẩn vào slot để lần sau khách hỏi "cấu hình nó" thì chính xác hơn
                events.append(SlotSet("product_name", item['name']))
            elif len(results) > 1:
                best_match = results[0]
                short_desc = (best_match['description'][:150] + '...') if len(best_match['description']) > 150 else best_match['description']
                names = ", ".join([r['name'] for r in results[1:]])

                msg = (f"Dạ, dòng '{raw_product_name}' shop có khá nhiều mẫu.\n\n"
                        f"🌟 **Nổi bật nhất** là {best_match['name']} với thông tin là **{short_desc}**.\n\n"
                        f"Ngoài ra, shop còn có: {names}. Bạn quan tâm mẫu nào trong số này ạ?")
                    
                dispatcher.utter_message(text=msg)
                events.append(SlotSet("product_name", best_match['name']))

        except mysql.connector.Error as err:
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

        try:
            cursor = connection.cursor(dictionary=True)
            # Sử dụng hàm helper chung để tìm kiếm sản phẩm
            raw_product_name, results = find_products_in_db(tracker, cursor)

            events = []

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
            if len(results) == 1:
                item = results[0]
                name = item['name']
                p_type = item['type'] # Lấy trường 'type' từ DB
                
                dispatcher.utter_message(
                    text=f"Dạ, sản phẩm **{name}** thuộc dòng **{p_type}** của shop mình ạ."
                )
                events.append(SlotSet("product_name", name))

            # TRƯỜNG HỢP 3: Tìm thấy nhiều sản phẩm tương tự
            elif len(results) > 1:
                best_match = results[0]
                p_type = best_match['type']
                others = ", ".join([r['name'] for r in results[1:4]]) # Lấy thêm tối đa 3 mẫu khác

                msg = (f"Dạ, mẫu '{best_match['name']}' mà bạn quan tâm thuộc dòng **{p_type}**.\n\n"
                       f"Trong dòng này shop còn có: {others}. Bạn có muốn xem chi tiết mẫu nào không?")
                
                dispatcher.utter_message(text=msg)
                events.append(SlotSet("product_name", best_match['name']))

        except mysql.connector.Error as err:
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
            dispatcher.utter_message(text="Rất xin lỗi, hệ thống dữ liệu của shop đang gặp chút trục trặc. Bạn thử lại sau nhé!")
        
        finally:
            # --- Đóng kết nối an toàn ---
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

        return []
