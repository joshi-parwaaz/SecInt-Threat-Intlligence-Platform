"""
services/classifier.py - NLP-based threat classification service

Consumes from Kafka, classifies threats, and writes to MongoDB
"""
import json
import os
import logging
from kafka import KafkaConsumer
from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import pickle
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/secint")

class ThreatClassifier:
    """Simple NLP-based threat classifier using TF-IDF + Naive Bayes"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.classifier = MultinomialNB()
        self.is_trained = False
        self.label_map = {
            0: "credential_leak",
            1: "exploit",
            2: "phishing",
            3: "malware",
            4: "unknown"
        }
    
    def train_simple_model(self):
        """Train a simple baseline model with synthetic examples"""
        # Minimal training data for demonstration
        training_texts = [
            "password leak database credentials stolen",
            "CVE exploit vulnerability remote code execution",
            "phishing email fake login page scam",
            "malware ransomware trojan virus infection",
            "unknown threat generic data"
        ]
        training_labels = [0, 1, 2, 3, 4]
        
        X = self.vectorizer.fit_transform(training_texts)
        self.classifier.fit(X, training_labels)
        self.is_trained = True
        logger.info("✅ Trained simple baseline classifier")
    
    def classify(self, text: str) -> tuple:
        """Classify a text and return (threat_type, confidence)"""
        if not self.is_trained:
            self.train_simple_model()
        
        if not text or len(text) < 10:
            return "unknown", 0.5
        
        X = self.vectorizer.transform([text])
        prediction = self.classifier.predict(X)[0]
        probabilities = self.classifier.predict_proba(X)[0]
        confidence = float(max(probabilities))
        
        threat_type = self.label_map.get(prediction, "unknown")
        
        return threat_type, confidence

class ClassificationService:
    """Service that consumes from Kafka and classifies threats"""
    
    def __init__(self):
        self.consumer = KafkaConsumer(
            "threat-intel-raw",
            bootstrap_servers=[KAFKA_BROKER],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='threat-classifier'
        )
        
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client['secint']
        self.threats_col = self.db['threats']
        self.logs_col = self.db['ingestion_logs']
        
        self.classifier = ThreatClassifier()
        self.classifier.train_simple_model()
    
    def process_message(self, message_value: dict):
        """Process a single Kafka message"""
        dataset = message_value.get("dataset", "unknown")
        data = message_value.get("data", {})
        
        # Extract text content (dataset-specific logic)
        text = self._extract_text(data, dataset)
        
        if not text:
            logger.warning(f"No text extracted from record in {dataset}")
            return
        
        # Classify
        threat_type, confidence = self.classifier.classify(text)
        
        # Build threat record
        threat_record = {
            "dataset": dataset,
            "threat_type": threat_type,
            "content": text[:5000],  # Limit content size
            "timestamp": datetime.utcnow(),
            "classification_confidence": confidence,
            "metadata": data
        }
        
        # Insert into MongoDB
        try:
            self.threats_col.insert_one(threat_record)
            logger.info(f"✅ Classified {dataset} record as {threat_type} (confidence: {confidence:.2f})")
        except Exception as e:
            logger.error(f"Failed to insert threat: {e}")
    
    def _extract_text(self, data: dict, dataset: str) -> str:
        """Extract relevant text from data based on dataset type"""
        # Dataset-specific text extraction logic
        if dataset == "phishing_emails":
            return data.get("email_body", data.get("subject", str(data)))
        elif dataset == "exploitdb":
            return data.get("description", data.get("title", str(data)))
        elif dataset == "open_malsec":
            return data.get("description", data.get("content", str(data)))
        elif dataset == "malware_motif":
            return data.get("family", data.get("description", str(data)))
        else:
            # Fallback: concatenate all string values
            return " ".join(str(v) for v in data.values() if isinstance(v, str))
    
    def run(self):
        """Start consuming and processing messages"""
        logger.info("🚀 Starting threat classification service...")
        logger.info(f"Kafka broker: {KAFKA_BROKER}")
        logger.info(f"MongoDB: {MONGO_URI}")
        
        try:
            for message in self.consumer:
                self.process_message(message.value)
        except KeyboardInterrupt:
            logger.info("Shutting down classifier service...")
        finally:
            self.consumer.close()
            self.mongo_client.close()

if __name__ == "__main__":
    service = ClassificationService()
    service.run()
