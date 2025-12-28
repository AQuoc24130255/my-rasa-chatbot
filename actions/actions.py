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


class ActionGetProductPrice(Action):
    def name(self) -> Text:
        return "action_get_product_price"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Lấy tên sản phẩm khách vừa nhắc tới (Entity: product_name)
        product_name = next(tracker.get_latest_entity_values("product_name"), None)

        if not product_name:
            dispatcher.utter_message(text="Bạn muốn hỏi giá của sản phẩm nào ạ? (Ví dụ: áo thun, quần jean)")
            return []

        try:
            # Kết nối Database (Dùng IP 127.0.0.1 để tránh lỗi socket)
            connection = mysql.connector.connect(
                host='127.0.0.1',
                user='gemini_user',
                password='123456',
                database='gemini_shop'
            )
            cursor = connection.cursor(dictionary=True)

            # Truy vấn tìm kiếm sản phẩm (dùng LIKE để tìm kiếm gần đúng)
            query = "SELECT name, price FROM products WHERE name LIKE %s LIMIT 1"
            cursor.execute(query, ("%" + product_name + "%",))
            result = cursor.fetchone()

            if result:
                name = result['name']
                price = "{:,.0f}".format(result['price']) # Định dạng 150,000
                dispatcher.utter_message(text=f"Dạ, sản phẩm {name} hiện có giá là {price} VNĐ ạ.")
            else:
                dispatcher.utter_message(text=f"Tiếc quá, hiện tại shop chưa có thông tin giá cho '{product_name}' ạ.")

        except mysql.connector.Error as err:
            dispatcher.utter_message(text="Rất xin lỗi, hệ thống dữ liệu của shop đang gặp chút trục trặc. Bạn thử lại sau nhé!")
        
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

        return []

class ActionGetProductDescription(Action):
    def name(self) -> Text:
        # Tên này phải trùng với khai báo trong domain.yml
        return "action_get_product_description"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # 1. Lấy thực thể product_name
        product_name = next(tracker.get_latest_entity_values("product_name"), None)

        if not product_name:
            dispatcher.utter_message(text="Bạn muốn xem thông tin chi tiết của sản phẩm nào ạ?")
            return []

        try:
            # 2. Kết nối MySQL
            connection = mysql.connector.connect(
                host='127.0.0.1',
                user='gemini_user',
                password='123456',
                database='gemini_shop'
            )
            cursor = connection.cursor(dictionary=True)

            # 3. Truy vấn lấy Description
            query = "SELECT name, description FROM products WHERE LOWER(name) LIKE LOWER(%s) LIMIT 1"
            cursor.execute(query, ("%" + product_name + "%",))
            result = cursor.fetchone()

            if result:
                name = result['name']
                desc = result['description']
                dispatcher.utter_message(text=f"Thông tin chi tiết về {name}: {desc}")
            else:
                dispatcher.utter_message(text=f"Xin lỗi, shop chưa có thông tin mô tả cho sản phẩm '{product_name}'.")

        except mysql.connector.Error as err:
            dispatcher.utter_message(text="Hệ thống đang gặp lỗi kết nối dữ liệu.")
        
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

        return []