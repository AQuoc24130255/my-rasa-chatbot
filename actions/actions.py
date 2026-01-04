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
        
class ActionGetProductPrice(Action):
    def name(self) -> Text:
        return "action_get_product_price"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        cursor = None
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
            connection = get_db_connection()
            if not connection:
                dispatcher.utter_message(text="Lỗi kết nối database.")
                return []
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
                
                if all_products: # Kiểm tra tránh crash nếu DB trống
                    choices = {p['search_name']: p for p in all_products}
                    # Sử dụng extractOne an toàn
                    match_result = process.extractOne(search_term, choices.keys(), scorer=fuzz.token_set_ratio)
                    if match_result and match_result[1] > 70:
                        results = [choices[match_result[0]]]
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
            connection = get_db_connection()
            if not connection:
                dispatcher.utter_message(text="Lỗi kết nối database.")
                return []
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
                cursor.execute("SELECT name, description, search_name FROM products")
                all_products = cursor.fetchall()
                
                if all_products: # Kiểm tra tránh crash nếu DB trống
                    choices = {p['search_name']: p for p in all_products}
                    # Sử dụng extractOne an toàn
                    match_result = process.extractOne(search_term, choices.keys(), scorer=fuzz.token_set_ratio)
                    if match_result and match_result[1] > 70:
                        results = [choices[match_result[0]]]
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
            # --- Đóng kết nối an toàn ---
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

        return events

class ActionGetProductCount(Action):
    def name(self) -> Text:
        return "action_get_product_count"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        cursor = None
        try:
            connection = get_db_connection()
            if not connection:
                dispatcher.utter_message(text="Lỗi kết nối database.")
                return []
            cursor = connection.cursor(dictionary=True)

            # Truy vấn đếm số lượng TÊN sản phẩm khác nhau
            query = "SELECT COUNT(DISTINCT name) as total FROM products"
            cursor.execute(query)
            result = cursor.fetchone()
            count = result['total'] if result else 0 # Gọi bằng key 'total'

            if count > 0:
                message = f"Dạ, hiện tại shop đang có tất cả **{count} mẫu sản phẩm** khác nhau để bạn lựa chọn ạ!"
                dispatcher.utter_message(text=message)
            else:
                dispatcher.utter_message(text="Dạ, hiện tại danh mục sản phẩm đang trống ạ.")

        except mysql.connector.Error as err:
            dispatcher.utter_message(text="Lỗi kết nối database khi đếm sản phẩm.")
        
        finally:
            # --- Đóng kết nối an toàn ---
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

        return []

class ActionCountProductByType(Action):
    def name(self) -> Text:
        return "action_count_product_by_type"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        cursor = None
        # 1. Lấy thực thể 'product_type' từ tin nhắn khách (ví dụ: "màn hình", "laptop")
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
                        {"title": f"Xem các mẫu {matched_type}", "payload": f"/search_product_by_type{{\"product_type\":\"{matched_type}\"}}"}
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

class ActionCountAllTypes(Action):
    def name(self) -> Text:
        return "action_count_all_types"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        cursor = None
        connection = get_db_connection()
        if not connection:
            dispatcher.utter_message(text="Lỗi kết nối database.")
            return []
        cursor = connection.cursor(dictionary=True)

        try:
            # 1. Truy vấn lấy danh sách các loại (type) duy nhất
            cursor.execute("SELECT DISTINCT type FROM products")
            rows = cursor.fetchall()
            
            types = [row['type'] for row in rows if row['type']]
            total_types = len(types)

            if total_types > 0:
                # 2. Tạo thông báo
                type_list_str = ", ".join(types)
                msg = f"Dạ, hiện tại Gemini Shop đang kinh doanh **{total_types}** dòng sản phẩm chính, bao gồm: {type_list_str}."
                dispatcher.utter_message(text=msg)

                # 3. Tạo các nút bấm để khách chọn xem loại nào luôn
                buttons = []
                for t in types:
                    buttons.append({
                        "title": f"Xem {t}",
                        "payload": f'/show_products_by_type{{"product_type": "{t}"}}'
                    })
                
                dispatcher.utter_message(text="Bạn muốn tham khảo dòng sản phẩm nào ạ?", buttons=buttons)
            else:
                dispatcher.utter_message(text="Hiện tại shop đang cập nhật danh mục sản phẩm, bạn vui lòng quay lại sau nhé!")

        except Exception as e:
            dispatcher.utter_message(text=f"Lỗi hệ thống khi đếm loại sản phẩm: {str(e)}")
        finally:
            # --- Đóng kết nối an toàn ---
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

        return []

class ActionShowAllProducts(Action):
    def name(self) -> Text:
        return "action_show_all_products"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        cursor = None
        try:
            # 1. Kết nối MySQL
            connection = get_db_connection()
            if not connection:
                dispatcher.utter_message(text="Lỗi kết nối database.")
                return []
            cursor = connection.cursor(dictionary=True)

            # 2. Truy vấn lấy danh sách các tên mẫu duy nhất
            query = "SELECT DISTINCT name FROM products"
            cursor.execute(query)
            results = cursor.fetchall()

            if results:
                # 3. Định dạng danh sách kết quả
                product_list = "\n- ".join([row['name'] for row in results])
                message = f"Dạ, hiện tại Gemini Shop đang có các mẫu sản phẩm sau ạ:\n- {product_list}"
                message += "\n\nBạn muốn hỏi chi tiết hoặc giá của mẫu nào thì nhắn mình nhé!"
                dispatcher.utter_message(text=message)
            else:
                dispatcher.utter_message(text="Hiện tại shop đang cập nhật mẫu mới, bạn vui lòng quay lại sau nha!")

        except mysql.connector.Error as err:
            dispatcher.utter_message(text="Hệ thống gặp sự cố khi lấy danh sách sản phẩm.")
        
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
                            "payload": f"/search_product{{\"product_name\":\"{p['name']}\"}}"
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

class ActionListProductTypes(Action):
    def name(self) -> Text:
        return "action_list_product_types"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        cursor = None
        connection = get_db_connection()
        if not connection:
            dispatcher.utter_message(text="Lỗi kết nối database.")
            return []
        cursor = connection.cursor(dictionary=True)

        try:
            # 1. Truy vấn các loại sản phẩm duy nhất
            cursor.execute("SELECT DISTINCT type FROM products")
            rows = cursor.fetchall()

            if rows:
                # 2. Chuẩn bị tin nhắn và các nút bấm
                dispatcher.utter_message(text="🛍️ Gemini Shop hiện có các dòng sản phẩm sau:")
                
                buttons = []
                for row in rows:
                    p_type = row['type']
                    # Khi nhấn nút, sẽ gửi intent kèm slot product_type
                    buttons.append({
                        "title": f"Dòng {p_type}",
                        "payload": f'/show_products_by_type{{"product_type": "{p_type}"}}'
                    })
                
                # 3. Gửi danh sách nút bấm về cho người dùng
                dispatcher.utter_message(buttons=buttons)
            else:
                dispatcher.utter_message(text="Dạ, hiện tại shop chưa có sản phẩm nào được phân loại ạ.")

        except Exception as e:
            dispatcher.utter_message(text=f"Lỗi truy xuất danh mục: {str(e)}")
        finally:
            # --- Đóng kết nối an toàn ---
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

        return []

