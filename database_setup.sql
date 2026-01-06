-- MySQL dump 10.13  Distrib 8.0.44, for Linux (x86_64)
--
-- Host: 127.0.0.1    Database: gemini_shop
-- ------------------------------------------------------
-- Server version	8.0.44-0ubuntu0.24.04.2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `price` decimal(15,2) NOT NULL,
  `description` text,
  `type` varchar(255) NOT NULL,
  `search_name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
INSERT INTO `products` VALUES (1,'Apple MacBook Air M4 (13 inch, 2025)',23990000.00,'mẫu laptop siêu mỏng nhẹ với chip M4 mạnh mẽ, màn hình Liquid Retina sắc nét và thời lượng pin cả ngày','Laptop','apple macbook air m4 13 inch 2025'),(2,'Corsair Vengeance RGB DDR5 32GB (2x16GB) 6400MHz',3200000.00,'Sở hữu tốc độ xử lý vượt trội và hệ thống chiếu sáng RGB tùy biến qua phần mềm iCUE, đây là lựa chọn hàng đầu cho các dàn máy gaming và đồ họa chuyên nghiệp năm 2026','RAM','corsair vengeance rgb ddr5 32gb 2x16gb 6400mhz'),(3,'ASUS ROG Strix GeForce RTX 5070 Ti',22500000.00,'Dòng card mới nhất kiến trúc Blackwell mang lại hiệu suất dò tia (ray-tracing) cực đỉnh và khả năng xử lý AI mạnh mẽ, giúp vận hành mượt mà các tựa game AAA ở độ phân giải 4K','Card','asus rog strix geforce rtx 5070 ti'),(4,'G.Skill Trident Z5 RGB DDR5 32GB (2x16GB) 6400MHz',3400000.00,'Nổi tiếng với thiết kế tản nhiệt cao cấp và khả năng ép xung ổn định, dòng RAM này là đối thủ trực tiếp của Corsair, mang đến hiệu suất tuyệt vời cho cả game thủ và người sáng tạo nội dung','RAM','g skill trident z5 rgb ddr5 32gb 2x16gb 6400mhz'),(5,'GIGABYTE AORUS GeForce RTX 5080 MASTER 16G',45900000.00,'Đây là một trong những phiên bản cao cấp nhất của dòng RTX 5080, với xung nhịp được ép sẵn (overclocked) và hệ thống tản nhiệt buồng hơi hiệu quả, đảm bảo hiệu năng tối đa cho các tác vụ đồ họa và gaming 4K','Card','gigabyte aorus geforce rtx 5080 master 16g'),(6,'Dell Alienware AW3423DWF QD-OLED',21000000.00,'Màn hình cong siêu rộng 34 inch sử dụng công nghệ QD-OLED tiên tiến, mang lại độ tương phản vô hạn, màu sắc chính xác và thời gian phản hồi cực nhanh, hoàn hảo cho trải nghiệm gaming đỉnh cao','Màn hình','dell alienware aw3423dwf qd oled'),(7,'ASUS ROG Swift OLED PG32UCDM',39990000.00,'Đây là mẫu màn hình chơi game 32 inch sử dụng tấm nền QD-OLED thế hệ mới với độ phân giải 4K và tần số quét siêu mượt 240Hz. Sản phẩm nổi bật với thời gian phản hồi cực nhanh 0.03ms cùng hệ thống tản nhiệt tiên tiến giúp giảm thiểu rủi ro hiện tượng lưu ảnh','Màn hình','asus rog swift oled pg32ucdm');
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-06 13:57:07
