# Add this near the top of dummy_model.py
MYSQL_SCHEMA = """
=== MySQL Database Schema ===

CREATE TABLE `dosen` (
  `id` varchar(8) NOT NULL,
  `nama` varchar(64) NOT NULL,
  `namaPT` varchar(64) DEFAULT NULL,
  `namaProdi` varchar(64) DEFAULT NULL,
  `jenisKelamin` varchar(16) DEFAULT NULL,
  `jabatanAkademik` varchar(32) DEFAULT NULL,
  `pendidikanTertinggi` varchar(8) DEFAULT NULL,
  `statusIkatanKerja` varchar(32) DEFAULT NULL,
  `statusAktivitas` varchar(64) DEFAULT NULL,
  `orcidId` varchar(50) DEFAULT NULL,
  `scholarId` varchar(50) DEFAULT NULL,
  `semanticScholarId` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `employeecontract` (
  `id` varchar(16) NOT NULL,
  `IdDosen` varchar(8) DEFAULT NULL,
  `faiss_id` varchar(16) DEFAULT NULL,
  `contractDate` date DEFAULT NULL,
  `baseSalary` int DEFAULT NULL,
  `signatory` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`)
  CONSTRAINT `fk_dosen` FOREIGN KEY (`idDosen`) REFERENCES `dosen` (`id`),
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `matakuliah` (
  `id` varchar(16) NOT NULL,
  `nama` varchar(128) DEFAULT NULL,
  `jumlahSKS` tinyint NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `meetingminutes` (
  `id` varchar(16) NOT NULL,
  `faiss_id` varchar(16) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `title` varchar(128) DEFAULT NULL,
  `projectID` varchar(8) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `mengajar` (
  `id` varchar(128) NOT NULL,
  `idDosen` varchar(8) DEFAULT NULL,
  `MataKuliahID` varchar(16) DEFAULT NULL,
  `tahunAkademikStart` int DEFAULT NULL,
  `tahunAkademikEnd` int DEFAULT NULL,
  `semester` varchar(8) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_dosen` (`idDosen`),
  KEY `idx_matakuliah` (`MataKuliahID`),
  CONSTRAINT `fk_dosen` FOREIGN KEY (`idDosen`) REFERENCES `dosen` (`id`),
  CONSTRAINT `fk_matakuliah` FOREIGN KEY (`MataKuliahID`) REFERENCES `matakuliah` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `project` (
  `id` varchar(16) NOT NULL,
  `title` varchar(64) DEFAULT NULL,
  `budget` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `projectassignment` (
  `id` varchar(16) NOT NULL,
  `idDosen` varchar(8) DEFAULT NULL,
  `projectID` varchar(16) DEFAULT NULL,
  `peran` varchar(16) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idDosen` (`idDosen`),
  KEY `projectID` (`projectID`),
  CONSTRAINT `projectassignment_ibfk_1` FOREIGN KEY (`idDosen`) REFERENCES `dosen` (`id`),
  CONSTRAINT `fk_project` FOREIGN KEY (`projectID`) REFERENCES `project` (`id`),
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
"""