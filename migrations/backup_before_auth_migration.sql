/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19  Distrib 10.11.19-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: db    Database: smartbase_db
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `Books`
--

DROP TABLE IF EXISTS `Books`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `Books` (
  `isbn` varchar(20) NOT NULL,
  `title` varchar(255) NOT NULL,
  `author` varchar(255) NOT NULL,
  `about` varchar(2048) DEFAULT NULL,
  `msrp` decimal(10,2) NOT NULL,
  `publication_date` date DEFAULT NULL,
  `genre_id` int DEFAULT NULL,
  PRIMARY KEY (`isbn`),
  KEY `genre_id` (`genre_id`),
  CONSTRAINT `Books_ibfk_1` FOREIGN KEY (`genre_id`) REFERENCES `Genres` (`genre_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Books`
--

LOCK TABLES `Books` WRITE;
/*!40000 ALTER TABLE `Books` DISABLE KEYS */;
INSERT INTO `Books` VALUES
('978-0060254926','Where the Wild Things Are','Maurice Sendak','A mischievous young boy named Max is sent to his room without supper, lets his imagination run wild, and sails to an island of monsters.',18.95,'1963-11-09',30),
('978-0062080363','American Gods','Neil Gaiman','An ex-convict released from prison finds himself working for a mysterious con man as old mythological deities walk the American landscape.',16.99,'2001-06-19',11),
('978-0261102217','The Hobbit','J.R.R. Tolkien','A comfort-loving hobbit gets swept into an unexpected quest with a wizard and a band of dwarves to reclaim stolen treasure from a dragon.',14.99,'1937-09-21',11),
('978-0307454546','The Girl with the Dragon Tattoo','Stieg Larsson','A disgraced journalist and a brilliant punk hacker team up to investigate a wealthy family disappearance spanning four decades.',15.95,'2005-08-01',12),
('978-0307474279','The Da Vinci Code','Dan Brown','A symbologist and a cryptologist race across Europe to decode a trail of religious mysteries linked to a shocking murder.',16.00,'2003-03-18',12),
('978-0307588371','Gone Girl','Gillian Flynn','On his fifth wedding anniversary, a man becomes the primary suspect when his wife mysteriously vanishes from their home.',16.00,'2012-05-24',12),
('978-0312924584','The Silence of the Lambs','Thomas Harris','A young FBI trainee seeks the guidance of an imprisoned, highly intelligent serial killer to track down another active murderer.',14.50,'1988-05-01',12),
('978-0345539434','Cosmos','Carl Sagan','A stunning voyage through space and time, illuminating the history of science, astronomy, and our place in the universe.',20.00,'1980-10-01',21),
('978-0375842207','The Book Thief','Markus Zusak','Narrated by Death, this story follows a foster girl in Nazi Germany who finds solace by stealing books and sharing them.',13.99,'2005-09-01',13),
('978-0385531139','The Martian','Andy Weir','An astronaut is accidentally stranded alone on Mars after a fierce dust storm and must use his ingenuity and scientific wit to survive.',16.00,'2014-02-11',10),
('978-0399159848','Big Little Lies','Liane Moriarty','Three mothers in a coastal town bond over young children, but their seemingly perfect lives unravel into a dark local murder investigation.',17.00,'2014-07-29',12),
('978-0399588176','Born a Crime','Trevor Noah','Comedian Trevor Noah recounts his turbulent childhood growing up biracial in South Africa during and right after apartheid.',18.00,'2016-11-15',20),
('978-0399590504','Educated','Tara Westover','A memoir about a young woman who grows up isolated from society by survivalist parents and eventually escapes to earn a PhD.',18.50,'2018-02-20',20),
('978-0441172719','Dune','Frank Herbert','Set on the desert planet Arrakis, this epic follows young Paul Atreides as his family accepts stewardship of the valuable spice resource, leading to betrayal and destiny.',18.99,'1965-08-01',10),
('978-0441569595','Neuromancer','William Gibson','A washed-up computer hacker is hired by a mysterious employer for one last dangerous run into cyberspace, shaping cyberpunk culture.',15.50,'1984-07-01',10),
('978-0451166890','The Pillars of the Earth','Ken Follett','A sweeping epic centered around the construction of a massive cathedral in a twelfth-century English town torn apart by civil war.',22.00,'1989-10-01',13),
('978-0553293357','Foundation','Isaac Asimov','A visionary mathematician uses psychohistory to predict the collapse of a galactic empire and creates a sanctuary of knowledge to shorten the coming dark age.',14.99,'1951-05-01',10),
('978-0553296983','The Diary of a Young Girl','Anne Frank','The authentic, deeply moving journal of a Jewish teenager hiding with her family from the Nazi regime in Amsterdam.',10.99,'1947-06-25',20),
('978-0553380163','A Brief History of Time','Stephen Hawking','A landmark exploration of cosmology, black holes, space-time, and the fundamental forces shaping our universe.',16.00,'1988-04-01',21),
('978-0553573404','Snow Crash','Neal Stephenson','In a futuristic corporate-franchised America, a hacker and pizza delivery driver investigates a computer virus that affects human brains.',17.25,'1992-06-01',10),
('978-0618249060','Silent Spring','Rachel Carson','A groundbreaking environmental science text examining the widespread impact of chemical pesticides on ecosystems and wildlife.',15.00,'1962-09-27',21),
('978-0684839395','The 7 Habits of Highly Effective People','Stephen Covey','A timeless, principle-centered approach for solving personal and professional problems and improving effectiveness.',18.00,'1989-08-15',22),
('978-0735211292','Atomic Habits','James Clear','A practical, actionable framework for building good habits, breaking bad ones, and mastering small behavioral changes.',16.00,'2018-10-16',22),
('978-0756404741','The Name of the Wind','Patrick Rothfuss','A notorious wizard, musician, and thief recounts the legendary hardships and triumphs of his youth in his own quiet tavern voice.',18.00,'2007-03-27',11),
('978-0765326357','The Way of Kings','Brandon Sanderson','Soldiers, slaves, and scholars navigate a massive, magical storm-torn continent caught in a cyclical war.',24.99,'2010-08-31',11),
('978-0765350381','Mistborn: The Final Empire','Brandon Sanderson','A crew of talented thieves plans an elaborate heist to overthrow an immortal ruler who has oppressed the world for a millennium.',16.50,'2006-07-17',11),
('978-1250080401','The Nightingale','Kristin Hannah','Two sisters living in German-occupied France display incredible courage and resilience as they navigate survival and resistance.',17.99,'2015-02-03',13),
('978-1455563920','Pachinko','Min Jin Lee','A multi-generational saga detailing the struggles and triumphs of a Korean immigrant family living in 20th-century Japan.',17.00,'2017-02-07',13),
('978-1501173219','All the Light We Cannot See','Anthony Doerr','The paths of a blind French girl and a young German soldier collide in occupied France during the turmoil of World War II.',18.00,'2014-05-06',13),
('978-1524763138','Becoming','Michelle Obama','The former First Lady shares her deep roots on the South Side of Chicago, balancing work, family, and life in the White House.',19.00,'2018-11-13',20);
/*!40000 ALTER TABLE `Books` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Genres`
--

DROP TABLE IF EXISTS `Genres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `Genres` (
  `genre_id` int NOT NULL,
  `genre_name` varchar(255) NOT NULL,
  `genre_parent_id` int DEFAULT NULL,
  PRIMARY KEY (`genre_id`),
  KEY `genre_parent_id` (`genre_parent_id`),
  CONSTRAINT `Genres_ibfk_1` FOREIGN KEY (`genre_parent_id`) REFERENCES `Genres` (`genre_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Genres`
--

LOCK TABLES `Genres` WRITE;
/*!40000 ALTER TABLE `Genres` DISABLE KEYS */;
INSERT INTO `Genres` VALUES
(1,'Fiction',NULL),
(2,'Non-Fiction',NULL),
(3,'Children\'s Books',NULL),
(10,'Science Fiction',1),
(11,'Fantasy',1),
(12,'Mystery & Thriller',1),
(13,'Historical Fiction',1),
(20,'Biography & Memoir',2),
(21,'Science & Nature',2),
(22,'Self-Help',2),
(30,'Picture Books',3);
/*!40000 ALTER TABLE `Genres` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Reviews`
--

DROP TABLE IF EXISTS `Reviews`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `Reviews` (
  `review_id` int NOT NULL AUTO_INCREMENT,
  `isbn` varchar(20) NOT NULL,
  `user_id` int NOT NULL,
  `review_score` int DEFAULT NULL,
  PRIMARY KEY (`review_id`),
  KEY `isbn` (`isbn`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `Reviews_ibfk_1` FOREIGN KEY (`isbn`) REFERENCES `Books` (`isbn`),
  CONSTRAINT `Reviews_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `User` (`user_id`),
  CONSTRAINT `Reviews_chk_1` CHECK ((`review_score` between 1 and 5))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Reviews`
--

LOCK TABLES `Reviews` WRITE;
/*!40000 ALTER TABLE `Reviews` DISABLE KEYS */;
INSERT INTO `Reviews` VALUES
(1,'978-0441172719',1,5),
(2,'978-0261102217',2,5);
/*!40000 ALTER TABLE `Reviews` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `User`
--

DROP TABLE IF EXISTS `User`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `User` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `user_name` varchar(255) NOT NULL,
  `user_email` varchar(255) NOT NULL,
  `user_password` varchar(255) NOT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `User`
--

LOCK TABLES `User` WRITE;
/*!40000 ALTER TABLE `User` DISABLE KEYS */;
INSERT INTO `User` VALUES
(1,'Alice Smith','alice@example.com','hashed_password_1'),
(2,'Bob Jones','bob@example.com','hashed_password_2');
/*!40000 ALTER TABLE `User` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-08 22:37:20
