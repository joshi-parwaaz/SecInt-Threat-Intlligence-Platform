"""
services/ingestion.py - Dataset ingestion service

Scans ./data for datasets and publishes to Kafka for processing
"""
import json
import csv
from pathlib import Path
from typing import List, Dict
from kafka import KafkaProducer
from kafka.errors import KafkaError
import os
import logging
from pymongo import MongoClient
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
DATA_DIR = Path("/app/data")  # Docker volume mount path
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/secint")

class DatasetIngestionService:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            max_request_size=10485760  # 10MB
        )
        # MongoDB sync client for logging ingestion runs
        try:
            self.mongo_client = MongoClient(MONGO_URI)
            self.mongo_db = self.mongo_client.get_database()
        except Exception:
            logger.warning('Could not connect to MongoDB for ingestion logs')
            self.mongo_client = None
            self.mongo_db = None
        self.datasets = ["open_malsec", "malware_motif", "phishing_emails", "exploitdb"]
    
    def ingest_dataset(self, dataset_name: str) -> Dict:
        """Ingest a single dataset"""
        dataset_path = DATA_DIR / dataset_name / "raw"
        
        if not dataset_path.exists():
            logger.warning(f"Dataset path not found: {dataset_path}")
            return {"dataset": dataset_name, "status": "not_found", "records_processed": 0, "records_failed": 0}
        
        records_sent = 0
        records_failed = 0
        failed_files = []
        
        # Process all JSON/JSONL/CSV files recursively in raw folder
        for file_path in dataset_path.rglob("*.json"):
            try:
                records = self._process_json_file(file_path, dataset_name)
                records_sent += len(records)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                records_failed += 1
                failed_files.append({
                    "file": str(file_path.relative_to(DATA_DIR)),
                    "error": str(e)[:200]  # Truncate long errors
                })
        
        for file_path in dataset_path.rglob("*.jsonl"):
            try:
                records = self._process_jsonl_file(file_path, dataset_name)
                records_sent += len(records)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                records_failed += 1
                failed_files.append({
                    "file": str(file_path.relative_to(DATA_DIR)),
                    "error": str(e)[:200]
                })
        
        for file_path in dataset_path.rglob("*.csv"):
            try:
                records = self._process_csv_file(file_path, dataset_name)
                records_sent += len(records)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                records_failed += 1
                failed_files.append({
                    "file": str(file_path.relative_to(DATA_DIR)),
                    "error": str(e)[:200]
                })
        
        logger.info(f"✅ Ingested {dataset_name}: {records_sent} records sent, {records_failed} failed")
        
        # Write ingestion log to MongoDB with detailed failure info
        log_doc = {
            "dataset": dataset_name,
            "records_processed": records_sent,
            "records_failed": records_failed,
            "failed_files": failed_files,
            "status": "completed" if records_failed == 0 else "completed_with_errors",
            "timestamp": datetime.utcnow()
        }
        if self.mongo_db is not None:
            try:
                self.mongo_db.ingestion_logs.insert_one(log_doc)
            except Exception as e:
                logger.warning(f"Failed to write ingestion log to MongoDB: {e}")

        return {
            "dataset": dataset_name,
            "records_processed": records_sent,
            "records_failed": records_failed,
            "failed_files": failed_files,
            "status": "completed" if records_failed == 0 else "completed_with_errors"
        }
    
    def _process_json_file(self, file_path: Path, dataset: str) -> List[Dict]:
        """Process a JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            records = [data]
        else:
            records = []
        
        for record in records:
            self._send_to_kafka(record, dataset)
        
        return records
    
    def _process_jsonl_file(self, file_path: Path, dataset: str) -> List[Dict]:
        """Process a JSONL file (newline-delimited JSON)"""
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    self._send_to_kafka(record, dataset)
                    records.append(record)
        return records
    
    def _process_csv_file(self, file_path: Path, dataset: str) -> List[Dict]:
        """Process a CSV file"""
        records = []
        # Increase CSV field size limit for large email content
        csv.field_size_limit(10485760)  # 10MB
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self._send_to_kafka(row, dataset)
                records.append(row)
        return records
    
    def _send_to_kafka(self, record: Dict, dataset: str):
        """Send a single record to Kafka"""
        message = {
            "dataset": dataset,
            "data": record
        }
        
        try:
            self.producer.send("threat-intel-raw", value=message)
        except KafkaError as e:
            logger.error(f"Kafka send failed: {e}")
            raise
    
    def ingest_all(self):
        """Ingest all configured datasets"""
        logger.info(f"Starting ingestion for {len(self.datasets)} datasets...")
        
        results = []
        total_processed = 0
        total_failed = 0
        
        for dataset in self.datasets:
            result = self.ingest_dataset(dataset)
            results.append(result)
            total_processed += result['records_processed']
            total_failed += result['records_failed']
        
        self.producer.flush()
        self.producer.close()
        
        logger.info(f"🎉 Ingestion complete: {total_processed} records processed, {total_failed} failed across {len(self.datasets)} datasets")
        
        return results

if __name__ == "__main__":
    service = DatasetIngestionService()
    results = service.ingest_all()
    
    print("\n📊 Ingestion Summary:")
    for r in results:
        status_icon = "✅" if r['records_failed'] == 0 else "⚠️"
        print(f"  {status_icon} {r['dataset']}: {r['records_processed']} records ({r['status']})")
        if r['records_failed'] > 0 and r.get('failed_files'):
            for fail in r['failed_files']:
                print(f"    ❌ {fail['file']}: {fail['error']}")
