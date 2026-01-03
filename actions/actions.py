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
import mysql.connector
from unidecode import unidecode
import re
from thefuzz import fuzz, process
from rasa_sdk.events import SlotSet


class ActionGetProductPrice(Action):
    def name(self) -> Text:
        return "action_get_product_price"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Lấy tên sản phẩm khách vừa nhắc tới (Entity: product_name)
        raw_product_name = next(tracker.get_latest_entity_values("product_name"), None)

        # lục lại trong bộ nhớ (Slot) nếu không có entity
        if not raw_product_name:
            raw_product_name = tracker.get_slot("product_name")

        if not raw_product_name:
            dispatcher.utter_message(text="Bạn muốn hỏi giá của sản phẩm nào ạ? (Ví dụ: iphone, apple)")
            return []

        search_term = unidecode(raw_product_name).lower()
        keywords = re.findall(r'\b\w+\b', search_term)

        if not keywords:
            dispatcher.utter_message(text="Shop chưa rõ tên sản phẩm bạn cần hỏi.")
            return []

        events = []

        try:
            # Kết nối Database (Dùng IP 127.0.0.1 để tránh lỗi socket)
            connection = mysql.connector.connect(
                host='127.0.0.1',
                user='gemini_user',
                password='123456',
                database='gemini_shop'
            )
            cursor = connection.cursor(dictionary=True)

            # CHIẾN THUẬT 1: SQL LIKE (ƯU TIÊN CHÍNH XÁC) ---
            # Tìm sản phẩm chứa từ thứ 1 VÀ từ thứ 2 VÀ từ thứ 3...
            query = "SELECT name, price, search_name FROM products WHERE "
            conditions = []
            params = []

            # Chỉ lấy tối đa 4 từ khóa quan trọng nhất để tìm kiếm không bị quá hẹp
            for word in keywords[:4]: 
                conditions.append("search_name LIKE %s")
                params.append(f"%{word}%")
            
            query += " AND ".join(conditions)
            query += " ORDER BY LENGTH(name) ASC LIMIT 3"

            cursor.execute(query, tuple(params))
            results = cursor.fetchall()
            # --- CHIẾN THUẬT 2: FUZZY MATCHING (CỨU CÁNH KHI SAI CHÍNH TẢ) ---
            if not results:
                # Lấy toàn bộ danh sách search_name từ DB để so sánh mờ
                cursor.execute("SELECT name, search_name, price FROM products")
                all_products = cursor.fetchall()
                
                choices = {p['search_name']: p for p in all_products}
                # Tìm kiếm mờ (lấy kết quả giống nhất)
                # scorer=fuzz.token_set_ratio giúp xử lý tốt việc đảo thứ tự từ
                best_match_key, score = process.extractOne(search_term, choices.keys(), scorer=fuzz.token_set_ratio)

                if score > 70:  # Ngưỡng tin cậy 70%
                    results = [choices[best_match_key]]
            '''
            # Truy vấn tìm kiếm sản phẩm (dùng LIKE để tìm kiếm gần đúng)
            query = """SELECT name, price FROM products 
                WHERE search_name LIKE %s 
                OR %s LIKE CONCAT('%', search_name, '%')
                ORDER BY LENGTH(search_name) DESC
                LIMIT 5
            """
            cursor.execute(query, ("%" + search_term + "%",search_term))
            results = cursor.fetchall()
            '''
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
            else:
                msg = (f"Tiếc quá, hiện tại shop chưa có thông tin giá cho '{raw_product_name}' ạ.\n\n"
                    "Bạn có muốn xem qua những mẫu máy đang sẵn hàng tại shop không?")
                # Gợi ý khách xem các sản phẩm khác bằng nút bấm
                buttons = [
                    {"title": "📦 Xem danh sách sản phẩm", "payload": "/ask_all_products"},
                    {"title": "🔍 Thử tìm tên khác", "payload": "/ask_price"},
                    {"title": "📞 Cần nhân viên gọi lại", "payload": "/out_of_scope"}
                ]
                dispatcher.utter_message(text=msg, buttons=buttons)
                events.append(SlotSet("product_name", None))

        except mysql.connector.Error as err:
            dispatcher.utter_message(text="Rất xin lỗi, hệ thống dữ liệu của shop đang gặp chút trục trặc. Bạn thử lại sau nhé!")
        
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

        return events

class ActionGetProductDescription(Action):
    def name(self) -> Text:
        # Tên này phải trùng với khai báo trong domain.yml
        return "action_get_product_description"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # 1. Lấy thực thể product_name
        raw_product_name = next(tracker.get_latest_entity_values("product_name"), None)

        # lục lại trong bộ nhớ (Slot) nếu không có entity
        if not raw_product_name:
            raw_product_name = tracker.get_slot("product_name")

        if not raw_product_name:
            dispatcher.utter_message(text="Bạn muốn xem thông tin chi tiết của sản phẩm nào ạ?")
            return []

        search_term = unidecode(raw_product_name).lower()
        keywords = re.findall(r'\b\w+\b', search_term)

        if not keywords:
            dispatcher.utter_message(text="Shop chưa rõ tên sản phẩm bạn cần hỏi.")
            return []

        events = []

        try:
            # 2. Kết nối MySQL
            connection = mysql.connector.connect(
                host='127.0.0.1',
                user='gemini_user',
                password='123456',
                database='gemini_shop'
            )
            cursor = connection.cursor(dictionary=True)

            # --- CHIẾN THUẬT 1: SQL LIKE (ƯU TIÊN CHÍNH XÁC) ---
            # Tìm sản phẩm chứa từ thứ 1 VÀ từ thứ 2 VÀ từ thứ 3...
            query = "SELECT name, description, search_name FROM products WHERE "
            conditions = []
            params = []

            # Chỉ lấy tối đa 4 từ khóa quan trọng nhất để tìm kiếm không bị quá hẹp
            for word in keywords[:4]: 
                conditions.append("search_name LIKE %s")
                params.append(f"%{word}%")
            
            query += " AND ".join(conditions)
            query += " ORDER BY LENGTH(name) ASC LIMIT 3"

            cursor.execute(query, tuple(params))
            results = cursor.fetchall()
            # --- CHIẾN THUẬT 2: FUZZY MATCHING (CỨU CÁNH KHI SAI CHÍNH TẢ) ---
            if not results:
                # Lấy toàn bộ danh sách search_name từ DB để so sánh mờ
                cursor.execute("SELECT name, search_name, price FROM products")
                all_products = cursor.fetchall()
                
                choices = {p['search_name']: p for p in all_products}
                # Tìm kiếm mờ (lấy kết quả giống nhất)
                # scorer=fuzz.token_set_ratio giúp xử lý tốt việc đảo thứ tự từ
                best_match_key, score = process.extractOne(search_term, choices.keys(), scorer=fuzz.token_set_ratio)

                if score > 70:  # Ngưỡng tin cậy 70%
                    results = [choices[best_match_key]]
            '''
            # 3. Truy vấn lấy Description
            query = """SELECT name, description FROM products 
                WHERE search_name LIKE %s 
                OR %s LIKE CONCAT('%', search_name, '%')
                ORDER BY LENGTH(search_name) DESC
                LIMIT 3
            """
            cursor.execute(query, ("%" + search_term + "%",search_term))
            results = cursor.fetchall()
            '''


            if len(results) == 1:
                item = results[0]
                name = item['name']
                desc = item['description']
                dispatcher.utter_message(text=f"Thông tin chi tiết về {name}: {desc}")
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
            else:
                dispatcher.utter_message(text=f"Xin lỗi, shop chưa có thông tin mô tả cho sản phẩm '{raw_product_name}'.")
                # Gợi ý khách xem các sản phẩm khác bằng nút bấm
                buttons = [
                    {"title": "📦 Xem danh sách sản phẩm", "payload": "/ask_all_products"},
                    {"title": "🔍 Thử tìm tên khác", "payload": "/ask_description"},
                    {"title": "📞 Cần nhân viên gọi lại", "payload": "/out_of_scope"}
                ]
                dispatcher.utter_message(text="Bạn có muốn xem qua những mẫu máy đang sẵn hàng tại shop không?", buttons=buttons)
                events.append(SlotSet("product_name", None))

        except mysql.connector.Error as err:
            dispatcher.utter_message(text="Hệ thống đang gặp lỗi kết nối dữ liệu.")
        
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

        return events

class ActionGetProductCount(Action):
    def name(self) -> Text:
        return "action_get_product_count"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        try:
            connection = mysql.connector.connect(
                host='127.0.0.1',
                user='gemini_user',
                password='123456',
                database='gemini_shop'
            )
            cursor = connection.cursor()

            # Truy vấn đếm số lượng TÊN sản phẩm khác nhau
            query = "SELECT COUNT(DISTINCT name) FROM products"
            cursor.execute(query)
            result = cursor.fetchone()
            
            # Lấy con số tổng
            distinct_names_count = result[0] if result else 0

            if distinct_names_count > 0:
                message = f"Dạ, hiện tại shop đang có tất cả **{distinct_names_count} mẫu sản phẩm** khác nhau để bạn lựa chọn ạ!"
                dispatcher.utter_message(text=message)
            else:
                dispatcher.utter_message(text="Dạ, hiện tại danh mục sản phẩm đang trống ạ.")

        except mysql.connector.Error as err:
            dispatcher.utter_message(text="Lỗi kết nối database khi đếm sản phẩm.")
        
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

        return []

class ActionShowAllProducts(Action):
    def name(self) -> Text:
        return "action_show_all_products"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        try:
            # 1. Kết nối MySQL
            connection = mysql.connector.connect(
                host='127.0.0.1',
                user='gemini_user',
                password='123456',
                database='gemini_shop'
            )
            cursor = connection.cursor()

            # 2. Truy vấn lấy danh sách các tên mẫu duy nhất
            query = "SELECT DISTINCT name FROM products"
            cursor.execute(query)
            results = cursor.fetchall()

            if results:
                # 3. Định dạng danh sách kết quả
                product_list = "\n- ".join([row[0] for row in results])
                message = f"Dạ, hiện tại Gemini Shop đang có các mẫu sản phẩm sau ạ:\n- {product_list}"
                message += "\n\nBạn muốn hỏi chi tiết hoặc giá của mẫu nào thì nhắn mình nhé!"
                dispatcher.utter_message(text=message)
            else:
                dispatcher.utter_message(text="Hiện tại shop đang cập nhật mẫu mới, bạn vui lòng quay lại sau nha!")

        except mysql.connector.Error as err:
            dispatcher.utter_message(text="Hệ thống gặp sự cố khi lấy danh sách sản phẩm.")
        
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

        return []

