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
-- Table structure for table `BIENTHESP`
--

DROP TABLE IF EXISTS `BIENTHESP`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `BIENTHESP` (
  `id_bienthe` int NOT NULL AUTO_INCREMENT,
  `id_sp` int NOT NULL,
  `sku` varchar(50) NOT NULL,
  `gia` decimal(15,2) NOT NULL,
  `thongsokythuat` json DEFAULT NULL,
  PRIMARY KEY (`id_bienthe`),
  UNIQUE KEY `sku` (`sku`),
  KEY `fk_bienthe_sp` (`id_sp`),
  CONSTRAINT `fk_bienthe_sp` FOREIGN KEY (`id_sp`) REFERENCES `SPCHINH` (`id_sp`) ON DELETE CASCADE,
  CONSTRAINT `BIENTHESP_chk_1` CHECK ((`gia` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=55 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `BIENTHESP`
--

LOCK TABLES `BIENTHESP` WRITE;
/*!40000 ALTER TABLE `BIENTHESP` DISABLE KEYS */;
INSERT INTO `BIENTHESP` VALUES (1,1,'COR-VNG-5-32B',3550000.00,'{\"bus\": \"6000MHz\", \"color\": \"Black\", \"capacity\": \"32GB\"}'),(2,1,'COR-VNG-5-32W',3700000.00,'{\"bus\": \"6000MHz\", \"color\": \"White\", \"capacity\": \"32GB\"}'),(3,2,'COR-LPX-4-16B',1250000.00,'{\"bus\": \"3200MHz\", \"color\": \"Black\", \"capacity\": \"16GB\"}'),(4,3,'COR-DOM-T-64B',6800000.00,'{\"bus\": \"7200MHz\", \"style\": \"Titanium\", \"capacity\": \"64GB\"}'),(5,4,'COR-VNG-S-16B',1100000.00,'{\"type\": \"SODIMM\", \"capacity\": \"16GB\"}'),(6,5,'COR-DOM-P-32B',4500000.00,'{\"bus\": \"5600MHz\", \"capacity\": \"32GB\"}'),(7,6,'KGN-BST-5-16',1850000.00,'{\"bus\": \"5200MHz\", \"capacity\": \"16GB\"}'),(8,6,'KGN-BST-5-32',3400000.00,'{\"bus\": \"5200MHz\", \"capacity\": \"32GB\"}'),(9,7,'KGN-RNG-5-32',4200000.00,'{\"bus\": \"7200MHz\", \"capacity\": \"32GB\"}'),(10,8,'KGN-IMP-S-16',1350000.00,'{\"type\": \"SODIMM\", \"capacity\": \"16GB\"}'),(11,9,'KGN-NV2-1TB',1650000.00,'{\"capacity\": \"1TB\", \"interface\": \"PCIe 4.0\"}'),(12,10,'KGN-BST-4-8',650000.00,'{\"bus\": \"3200MHz\", \"capacity\": \"8GB\"}'),(13,11,'GSK-Z5R-32B',3900000.00,'{\"bus\": \"6000MHz\", \"color\": \"Black\", \"capacity\": \"32GB\"}'),(14,11,'GSK-Z5R-32S',4050000.00,'{\"bus\": \"6000MHz\", \"color\": \"Silver\", \"capacity\": \"32GB\"}'),(15,12,'GSK-RS5-32',3200000.00,'{\"style\": \"Low-profile\", \"capacity\": \"32GB\"}'),(16,13,'GSK-ZRY-32G',5500000.00,'{\"finish\": \"Gold\", \"capacity\": \"32GB\"}'),(17,14,'GSK-FX5-32A',3350000.00,'{\"capacity\": \"32GB\", \"optimization\": \"AMD EXPO\"}'),(18,15,'GSK-RV4-16',1150000.00,'{\"bus\": \"3200MHz\", \"capacity\": \"16GB\"}'),(19,15,'GSK-RV4-32',2100000.00,'{\"bus\": \"3200MHz\", \"capacity\": \"32GB\"}'),(20,16,'INT-14900K-B',15800000.00,'{\"type\": \"Box\", \"warranty\": \"36m\"}'),(21,16,'INT-14900K-T',14900000.00,'{\"type\": \"Tray\", \"warranty\": \"12m\"}'),(22,17,'INT-14700K-B',11200000.00,'{\"type\": \"Box\"}'),(23,18,'INT-13400F-B',5100000.00,'{\"gpu\": \"None\"}'),(24,19,'INT-12100-B',2800000.00,'{\"gpu\": \"UHD 730\"}'),(25,20,'INT-ULT-9-B',16500000.00,'{\"ai\": \"NPU Integrated\"}'),(26,21,'AMD-7950X3D',17500000.00,'{\"cache\": \"128MB L3\"}'),(27,22,'AMD-7800X3D',11500000.00,'{\"cache\": \"96MB L3\"}'),(28,23,'AMD-7600-B',5500000.00,'{\"socket\": \"AM5\"}'),(29,24,'AMD-5900X-B',8500000.00,'{\"socket\": \"AM4\"}'),(30,25,'AMD-5700G-B',4800000.00,'{\"igpu\": \"Radeon Graphics\"}'),(31,26,'APL-M4-10C',5000000.00,'{\"cpu_cores\": 10}'),(32,27,'APL-M3P-12C',7500000.00,'{\"cpu_cores\": 12}'),(33,28,'APL-M3X-16C',12000000.00,'{\"cpu_cores\": 16}'),(34,29,'APL-M2A-8C',4000000.00,'{\"cpu_cores\": 8}'),(35,30,'APL-M1U-20C',18000000.00,'{\"cpu_cores\": 20}'),(40,31,'ASU-STX-4090',58000000.00,'{\"vram\": \"24GB\", \"edition\": \"OC\"}'),(41,32,'ASU-TUF-4070T',24500000.00,'{\"vram\": \"12GB\", \"edition\": \"Gaming\"}'),(42,33,'ASU-DUA-4060',8500000.00,'{\"fans\": 2, \"vram\": \"8GB\"}'),(43,34,'ASU-PRO-4080',32000000.00,'{\"vram\": \"16GB\", \"target\": \"Creator\"}'),(44,35,'ASU-PHX-1650',3800000.00,'{\"vram\": \"4GB\", \"power\": \"No Pin\"}'),(45,36,'MSI-SUP-4080S',34500000.00,'{\"led\": \"RGB\", \"vram\": \"16GB\"}'),(46,37,'MSI-SLM-4070',18900000.00,'{\"vram\": \"12GB\", \"design\": \"Slim\"}'),(47,38,'MSI-VTS-4060',8200000.00,'{\"vram\": \"8GB\", \"series\": \"Ventus\"}'),(48,39,'MSI-TRI-7900X',28000000.00,'{\"gpu\": \"AMD\", \"vram\": \"24GB\"}'),(49,40,'MSI-GT-1030',2100000.00,'{\"vram\": \"2GB\", \"cooling\": \"Passive\"}'),(50,41,'GIG-AOR-4090',62000000.00,'{\"vram\": \"24GB\", \"screen\": \"LCD\"}'),(51,42,'GIG-EAG-4070',17500000.00,'{\"oc\": true, \"vram\": \"12GB\"}'),(52,43,'GIG-GOC-4060T',11800000.00,'{\"fans\": 3, \"vram\": \"8GB\"}'),(53,44,'GIG-GOC-7600T',9500000.00,'{\"vram\": \"16GB\"}'),(54,45,'GIG-WDF-3050',5900000.00,'{\"vram\": \"8GB\"}');
/*!40000 ALTER TABLE `BIENTHESP` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `DANHMUC`
--

DROP TABLE IF EXISTS `DANHMUC`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DANHMUC` (
  `id_loai` int NOT NULL AUTO_INCREMENT,
  `ten_loai` varchar(100) NOT NULL,
  PRIMARY KEY (`id_loai`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `DANHMUC`
--

LOCK TABLES `DANHMUC` WRITE;
/*!40000 ALTER TABLE `DANHMUC` DISABLE KEYS */;
INSERT INTO `DANHMUC` VALUES (1,'RAM'),(2,'CPU'),(3,'Card đồ họa');
/*!40000 ALTER TABLE `DANHMUC` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `SPCHINH`
--

DROP TABLE IF EXISTS `SPCHINH`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SPCHINH` (
  `id_sp` int NOT NULL AUTO_INCREMENT,
  `id_loai` int NOT NULL,
  `id_thuonghieu` int NOT NULL,
  `ten` varchar(255) NOT NULL,
  `mota` text,
  PRIMARY KEY (`id_sp`),
  KEY `fk_sp_danhmuc` (`id_loai`),
  KEY `fk_sp_thuonghieu` (`id_thuonghieu`),
  CONSTRAINT `fk_sp_danhmuc` FOREIGN KEY (`id_loai`) REFERENCES `DANHMUC` (`id_loai`) ON DELETE CASCADE,
  CONSTRAINT `fk_sp_thuonghieu` FOREIGN KEY (`id_thuonghieu`) REFERENCES `THUONGHIEU` (`id_thuonghieu`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SPCHINH`
--

LOCK TABLES `SPCHINH` WRITE;
/*!40000 ALTER TABLE `SPCHINH` DISABLE KEYS */;
INSERT INTO `SPCHINH` VALUES (1,1,1,'Vengeance RGB DDR5','RAM hiệu năng cao với hệ thống chiếu sáng RGB 10 vùng động và tần số cực nhanh cho PC hiện đại.'),(2,1,1,'Vengeance LPX DDR4','Thiết kế tản nhiệt nhôm tinh khiết giúp tản nhiệt nhanh hơn, phù hợp cho các hệ thống PC nhỏ gọn hoặc ép xung.'),(3,1,1,'Dominator Titanium','Dòng RAM DDR5 cao cấp nhất với khả năng tùy biến nắp trên, linh kiện chọn lọc kỹ lưỡng cho hiệu suất tối đa.'),(4,1,1,'Vengeance SODIMM (Laptop)','Giải pháp nâng cấp bộ nhớ tối ưu cho laptop gaming và máy trạm, đảm bảo độ ổn định và tương thích cao.'),(5,1,1,'Dominator Platinum RGB','Biểu tượng của sự sang trọng với công nghệ làm mát DHX độc quyền và 12 đèn LED CAPELLIX siêu sáng.'),(6,1,2,'FURY Beast DDR5','Mang lại tốc độ vượt trội cho các nền tảng chơi game thế hệ mới, hỗ trợ Intel XMP 3.0 và AMD EXPO.'),(7,1,2,'FURY Renegade','Dòng RAM hiệu năng cực cao dành cho game thủ và người sáng tạo nội dung, hỗ trợ tốc độ bus lên đến 8000MT/s.'),(8,1,2,'FURY Impact (Laptop)','Bộ nhớ chuẩn SODIMM mạnh mẽ, tự động ép xung (Plug N Play) để nâng cấp tức thì cho Laptop gaming.'),(9,1,2,'NV2 PCIe 4.0','Ổ cứng SSD chuẩn NVMe thế hệ 4.0 cung cấp tốc độ đọc/ghi cao, một giải pháp lưu trữ tối ưu từ thương hiệu con của Kingston.'),(10,1,2,'FURY Beast DDR4','Lựa chọn nâng cấp hoàn hảo cho các hệ thống DDR4 với thiết kế tản nhiệt đơn giản, hiệu quả và độ tin cậy cao.'),(11,1,3,'Trident Z5 RGB','Dòng RAM DDR5 biểu tượng với thanh sáng RGB rực rỡ, được thiết kế cho hiệu suất cực cao trên nền tảng Intel.'),(12,1,3,'Ripjaws S5','Dòng RAM DDR5 cấu hình thấp (low-profile), lý tưởng cho các hệ thống PC sử dụng tản nhiệt khí lớn hoặc không gian hẹp.'),(13,1,3,'Trident Z Royal','Sự kết hợp hoàn hảo giữa công nghệ và nghệ thuật với dải đèn tinh thể pha lê và lớp hoàn thiện mạ vàng/bạc sang trọng.'),(14,1,3,'Flare X5 (AMD)','Được tối ưu hóa hoàn toàn cho nền tảng AMD AM5 với cấu hình ép xung AMD EXPO, mang lại sự ổn định tuyệt đối.'),(15,1,3,'Ripjaws V DDR4','Lựa chọn kinh điển cho người dùng DDR4 với tản nhiệt hình răng cưa hầm hố, cung cấp hiệu suất đáng tin cậy trong nhiều năm.'),(16,2,4,'Core i9-14900K','CPU Flagship thế hệ 14 với 24 nhân và tốc độ lên tới 6.0 GHz, dành cho game thủ và chuyên gia xử lý đồ họa.'),(17,2,4,'Core i7-14700K','Sở hữu 20 nhân mạnh mẽ, là lựa chọn cân bằng nhất cho nhu cầu làm việc đa nhiệm và chơi game cao cấp.'),(18,2,4,'Core i5-13400F','CPU quốc dân phân khúc tầm trung, tối ưu chi phí cho game thủ khi không tích hợp nhân đồ họa nhưng vẫn đảm bảo hiệu suất.'),(19,2,4,'Core i3-12100','CPU 4 nhân hiệu quả cho các dàn PC văn phòng và chơi game nhẹ, dẫn đầu phân khúc giá rẻ về sức mạnh đơn nhân.'),(20,2,4,'Core Ultra 9 285K','Thế hệ vi xử lý hoàn toàn mới tích hợp NPU dành riêng cho AI, mang lại hiệu quả năng lượng đột phá trên nền tảng socket mới.'),(21,2,5,'Ryzen 9 7950X3D','CPU chơi game mạnh mẽ nhất của AMD với công nghệ 3D V-Cache đột phá, sở hữu 16 nhân và 32 luồng xử lý.'),(22,2,5,'Ryzen 7 7800X3D','Vị vua của phân khúc CPU gaming nhờ bộ nhớ đệm L3 cực lớn, mang lại tốc độ khung hình vượt trội trong mọi tựa game.'),(23,2,5,'Ryzen 5 7600','CPU 6 nhân thế hệ Zen 4 tối ưu về giá thành và hiệu năng, là lựa chọn tuyệt vời để bắt đầu với nền tảng socket AM5.'),(24,2,5,'Ryzen 9 5900X','Siêu phẩm đa nhân thế hệ Zen 3 vẫn cực kỳ mạnh mẽ cho các công việc đồ họa, dựng phim và làm việc chuyên nghiệp.'),(25,2,5,'Ryzen 7 5700G','CPU tích hợp nhân đồ họa Radeon mạnh nhất phân khúc, cho phép chơi game mượt mà mà không cần card đồ họa rời.'),(26,2,6,'Chip M4','Thế hệ chip mới nhất dựa trên tiến trình 3nm thứ hai, tối ưu cho AI và hiệu năng đơn nhân vượt trội.'),(27,2,6,'Chip M3 Pro','Sự cân bằng hoàn hảo giữa hiệu suất và tiết kiệm điện, lý tưởng cho người dùng sáng tạo chuyên nghiệp.'),(28,2,6,'Chip M3 Max','Sức mạnh đồ họa khủng khiếp với tối đa 40 nhân GPU, chuyên dụng cho dựng phim 8K và render 3D nặng.'),(29,2,6,'Chip M2 Air','Dòng chip tối ưu cho sự mỏng nhẹ, mang lại thời lượng pin ấn tượng và tốc độ xử lý nhanh hơn 18% so với M1.'),(30,2,6,'Chip M1 Ultra','Kiến trúc UltraFusion kết nối hai chip M1 Max, tạo ra sức mạnh tính toán khổng lồ cho các máy trạm Mac Studio.'),(31,3,7,'ROG Strix RTX 4090','Đỉnh cao đồ họa với thiết kế hầm hố, tản nhiệt 3 quạt Axial-tech và hiệu năng Ray Tracing không đối thủ.'),(32,3,7,'TUF Gaming RTX 4070 Ti','Độ bền chuẩn quân đội với khung kim loại và linh kiện cao cấp, mang lại hiệu suất chơi game 2K ổn định.'),(33,3,7,'Dual RTX 4060','Thiết kế nhỏ gọn 2 quạt phù hợp cho các dàn PC mini-ITX nhưng vẫn sở hữu sức mạnh từ kiến trúc Ada Lovelace.'),(34,3,7,'ProArt RTX 4080','Dòng card chuyên dụng cho thiết kế với vẻ ngoài tối giản, sang trọng và hệ thống tản nhiệt hoạt động cực kỳ yên tĩnh.'),(35,3,7,'Phoenix GTX 1650','Giải pháp đồ họa nhỏ gọn, tiết kiệm điện năng cho các hệ thống PC văn phòng cần bổ sung sức mạnh xử lý hình ảnh.'),(36,3,8,'GeForce RTX 4080 Super Suprim X','Dòng card đồ họa cao cấp nhất của MSI với lớp vỏ nhôm phay xước, tản nhiệt buồng hơi và hiệu năng ép xung đỉnh cao.'),(37,3,8,'RTX 4070 Gaming X Slim','Thiết kế mỏng nhẹ hơn nhưng vẫn giữ được hiệu suất mạnh mẽ và hệ thống tản nhiệt TRI FROZR 3 danh tiếng.'),(38,3,8,'RTX 4060 Ventus 2X','Sự lựa chọn tối ưu cho phân khúc phổ thông với thiết kế 2 quạt hiệu quả, tập trung vào giá trị cốt lõi và độ ổn định.'),(39,3,8,'Radeon RX 7900 XTX Gaming Trio','Siêu phẩm sử dụng kiến trúc AMD RDNA 3 với bộ nhớ VRAM khổng lồ 24GB, thách thức mọi tựa game ở độ phân giải 4K.'),(40,3,8,'GeForce GT 1030','Giải pháp xuất hình và xử lý đa phương tiện cơ bản, phù hợp cho các bộ máy văn phòng hoặc HTPC nhỏ gọn.'),(41,3,9,'RTX 4090 AORUS Master','Card đồ họa đỉnh bảng tích hợp màn hình LCD Edge View hiển thị thông số và hệ thống tản nhiệt Bionic Shark.'),(42,3,9,'RTX 4070 EAGLE OC','Thiết kế mạnh mẽ với tông màu xám lạnh, trang bị sẵn cấu hình ép xung từ nhà máy cho hiệu năng ổn định.'),(43,3,9,'RTX 4060 Ti Gaming OC','Dòng card quốc dân với tản nhiệt 3 quạt Windforce, mang lại sự cân bằng hoàn hảo giữa nhiệt độ và hiệu suất.'),(44,3,9,'Radeon RX 7600 XT Gaming OC','Giải pháp đồ họa 16GB VRAM từ đội đỏ AMD, tối ưu cho việc chơi game và xử lý video ở độ phân giải Full HD+.'),(45,3,9,'GeForce RTX 3050 Windforce','Lựa chọn nhập môn cho công nghệ Ray Tracing với giá thành dễ tiếp cận và hệ thống làm mát 2 quạt êm ái.');
/*!40000 ALTER TABLE `SPCHINH` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `THUOCTINHSP`
--

DROP TABLE IF EXISTS `THUOCTINHSP`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `THUOCTINHSP` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_bienthe` int NOT NULL,
  `tenthuoctinh` varchar(50) NOT NULL,
  `giatri` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_thuoctinh_bienthe` (`id_bienthe`),
  CONSTRAINT `fk_thuoctinh_bienthe` FOREIGN KEY (`id_bienthe`) REFERENCES `BIENTHESP` (`id_bienthe`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `THUOCTINHSP`
--

LOCK TABLES `THUOCTINHSP` WRITE;
/*!40000 ALTER TABLE `THUOCTINHSP` DISABLE KEYS */;
INSERT INTO `THUOCTINHSP` VALUES (1,1,'Dung lượng','32GB'),(2,1,'Bus','6000MHz'),(3,1,'Màu sắc','Đen'),(4,2,'Dung lượng','32GB'),(5,2,'Bus','6000MHz'),(6,2,'Màu sắc','Trắng'),(7,4,'Dung lượng','64GB'),(8,4,'Bus','7200MHz'),(9,13,'Dung lượng','32GB'),(10,13,'Bus','6000MHz'),(11,13,'Chuẩn','DDR5'),(12,20,'Số nhân','24'),(13,20,'Socket','LGA1700'),(14,20,'Kiểu đóng gói','Full Box'),(15,26,'Số nhân','16'),(16,26,'Socket','AM5'),(17,26,'Công nghệ','3D V-Cache'),(18,31,'Số nhân CPU','10-Core'),(19,31,'Tiến trình','3nm'),(20,40,'Dung lượng VRAM','24GB'),(21,40,'Thương hiệu GPU','NVIDIA'),(22,40,'Phiên bản','OC Edition'),(23,48,'Dung lượng VRAM','24GB'),(24,48,'Thương hiệu GPU','AMD'),(25,50,'Dung lượng VRAM','24GB'),(26,50,'Tính năng','Màn hình LCD');
/*!40000 ALTER TABLE `THUOCTINHSP` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `THUONGHIEU`
--

DROP TABLE IF EXISTS `THUONGHIEU`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `THUONGHIEU` (
  `id_thuonghieu` int NOT NULL AUTO_INCREMENT,
  `ten` varchar(100) NOT NULL,
  `slug` varchar(100) NOT NULL,
  PRIMARY KEY (`id_thuonghieu`),
  UNIQUE KEY `slug` (`slug`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `THUONGHIEU`
--

LOCK TABLES `THUONGHIEU` WRITE;
/*!40000 ALTER TABLE `THUONGHIEU` DISABLE KEYS */;
INSERT INTO `THUONGHIEU` VALUES (1,'Corsair','corsair'),(2,'Kingston','kingston'),(3,'G.Skill','g-skill'),(4,'Intel','intel'),(5,'AMD','amd'),(6,'Apple','apple'),(7,'ASUS','asus'),(8,'MSI','msi'),(9,'Gigabyte','gigabyte');
/*!40000 ALTER TABLE `THUONGHIEU` ENABLE KEYS */;
UNLOCK TABLES;

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

--
-- Temporary view structure for view `view_chi_tiet_san_pham`
--

DROP TABLE IF EXISTS `view_chi_tiet_san_pham`;
/*!50001 DROP VIEW IF EXISTS `view_chi_tiet_san_pham`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `view_chi_tiet_san_pham` AS SELECT 
 1 AS `id_sp`,
 1 AS `id_bienthe`,
 1 AS `ten_san_pham`,
 1 AS `sku`,
 1 AS `ten_loai`,
 1 AS `ten_thuonghieu`,
 1 AS `gia`,
 1 AS `mo_ta`,
 1 AS `thongsokythuat`*/;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `view_chi_tiet_san_pham`
--

/*!50001 DROP VIEW IF EXISTS `view_chi_tiet_san_pham`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`gemini_user`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `view_chi_tiet_san_pham` AS select `s`.`id_sp` AS `id_sp`,`b`.`id_bienthe` AS `id_bienthe`,`s`.`ten` AS `ten_san_pham`,`b`.`sku` AS `sku`,`d`.`ten_loai` AS `ten_loai`,`t`.`ten` AS `ten_thuonghieu`,`b`.`gia` AS `gia`,`s`.`mota` AS `mo_ta`,`b`.`thongsokythuat` AS `thongsokythuat` from (((`SPCHINH` `s` join `BIENTHESP` `b` on((`s`.`id_sp` = `b`.`id_sp`))) join `DANHMUC` `d` on((`s`.`id_loai` = `d`.`id_loai`))) join `THUONGHIEU` `t` on((`s`.`id_thuonghieu` = `t`.`id_thuonghieu`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-31 17:05:23
