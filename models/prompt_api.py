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
  `pendidikanTertinggi` varchar(8) DEFAULT NULL ["S1","S2","S3"],
  `statusIkatanKerja` varchar(32) DEFAULT NULL,
  `statusAktivitas` varchar(64) DEFAULT NULL ['Aktif', 'Tugas Belajar'],
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

MONGODB_PARTNERSHIP_SCHEMA = """
MONGODB PARTNERSHIP COLLECTION — `news`

Each document represents a crawled news/article page about a Telkom University
partnership event (MOU signing, collaboration announcement, etc.).

Fields used by this system:
  - partner_name  (str)  : Full name of the partner institution
                           e.g. "Universitas Borneo Tarakan"
  - title         (str)  : Page / article title
                           e.g. "Penandatanganan MOU Telkom University & ..."
  - summary       (str)  : Short auto-generated summary of the article
  - clean_text    (str)  : Full cleaned article body (used for FAISS content)
  - faiss_id      (int)  : ID into the shared FAISS vector index
  - partner_id    (int)  : Numeric ID for the partner institution

Typical query patterns:
  - Find by partner name  → filter on partner_name  (regex / $regex)
  - Find by keyword       → filter on title or summary ($regex)
  - Find by partner_id    → exact match on partner_id
  - Fetch docs by faiss_ids → filter on faiss_id: {$in: [...]}
  - use faiss for semantic search, then get partner_name for context using fiass_id
"""

WIKIBASE_SCHEMA = """
WIKIBASE KNOWLEDGE GRAPH SCHEMA:

Properties:
- P1 (Has Researched): Lecturer -> wdt:P1 -> Paper
- P2 (Has Patent): Lecturer -> wdt:P2 -> Patent
- P3 (is Lecturer): Entity -> wdt:P3 -> [] (Type check)
- P4 (is Paper): Entity -> wdt:P4 -> [] (Type check)
- P5 (is Patent): Entity -> wdt:P5 -> [] (Type check)
- P6 (Has Partnership): Institution -> wdt:P6 -> Partner
- P7 (Has Faculty): Institution -> wdt:P7 -> Faculty
- P8 (Affiliation): Person -> wdt:P8 -> Organization

SPARQL Prefixes:
PREFIX wd:       <http://38.147.122.59/entity/>
PREFIX wdt:      <http://38.147.122.59/prop/direct/>
PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wikibase: <http://wikiba.se/ontology#>
"""

FAISS_SCHEMA = """
FAISS VECTOR DATABASE:
Contains document content from:
- Meeting minutes (full text, agenda, decisions, action items)
- Employment contracts (terms, conditions, salary details)

Metadata (JSON) includes:
- faiss_id: unique identifier
- document_content: full document text
"""

MONGO_FULL_SCHEMA = """
collection : news
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": [
    "_id",
    "canonical_url",
    "clean_text",
    "content_hash",
    "context_specific_highlights",
    "country_hint",
    "crawl_time",
    "credibility_tier",
    "doc_id",
    "domain",
    "extracted_entities",
    "faiss_id",
    "language",
    "last_modified",
    "news_category",
    "out_links",
    "partner_id",
    "partner_name",
    "published_time",
    "raw_html",
    "risk_tags",
    "source_type",
    "summary",
    "title",
    "url"
  ],
  "properties": {
    "_id": {
      "$ref": "#/$defs/ObjectId"
    },
    "canonical_url": {
      "type": "string"
    },
    "clean_text": {
      "type": "string"
    },
    "content_hash": {
      "type": "string"
    },
    "context_specific_highlights": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "country_hint": {
      "type": [
        "string",
        "null"
      ]
    },
    "crawl_time": {
      "$ref": "#/$defs/Date"
    },
    "credibility_tier": {
      "type": "string"
    },
    "doc_id": {
      "type": "string"
    },
    "domain": {
      "type": "string"
    },
    "extracted_entities": {
      "type": "object",
      "required": [
        "companies",
        "locations",
        "persons"
      ],
      "properties": {
        "companies": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "locations": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "persons": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      }
    },
    "faiss_id": {
      "type": "integer"
    },
    "language": {
      "type": "string"
    },
    "last_modified": {
      "type": [
        "null",
        "string"
      ]
    },
    "news_category": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "out_links": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "partner_id": {
      "type": "integer"
    },
    "partner_name": {
      "type": "string"
    },
    "published_time": {
      "anyOf": [
        {
          "type": "null"
        },
        {
          "type": "string"
        },
        {
          "$ref": "#/$defs/Date"
        }
      ]
    },
    "raw_html": {
      "type": "string"
    },
    "risk_tags": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "source_type": {
      "type": "string"
    },
    "summary": {
      "type": "string"
    },
    "title": {
      "type": "string"
    },
    "url": {
      "type": "string"
    }
  },
  "$defs": {
    "ObjectId": {
      "type": "object",
      "properties": {
        "$oid": {
          "type": "string",
          "pattern": "^[0-9a-fA-F]{24}$"
        }
      },
      "required": [
        "$oid"
      ],
      "additionalProperties": false
    },
    "Date": {
      "type": "object",
      "properties": {
        "$date": {
          "type": "string",
          "format": "date-time"
        }
      },
      "required": [
        "$date"
      ],
      "additionalProperties": false
    }
  }
}
"""