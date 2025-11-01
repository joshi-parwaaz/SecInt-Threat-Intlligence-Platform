"""
Direct Threat Intelligence Ingestion Service - SecInt v2 (Localhost Version)
Fetches data from threat feeds and stores directly in MongoDB (no Kafka).
"""
import asyncio
import os
import sys
import logging
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.threat_feeds import threat_feeds
from services.enricher import enricher
from services.severity_scorer import severity_scorer
from database import connect_db, disconnect_db, get_collection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class DirectThreatIngestionService:
    """
    Simplified ingestion service that stores IOCs directly to MongoDB.
    No Kafka - runs synchronously for localhost development.
    """
    
    def __init__(self):
        self.stats = {
            'otx_pulses': 0,
            'urlhaus_urls': 0,
            'urlhaus_payloads': 0,
            'iocs_stored': 0,
            'iocs_enriched': 0,
            'failed_stores': 0
        }
    
    async def store_ioc(self, ioc_data: dict) -> bool:
        """
        Store IOC directly to MongoDB with enrichment and severity scoring.
        
        Args:
            ioc_data: Dictionary containing IOC information
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            collection = get_collection("iocs")
            
            # Check if IOC already exists
            existing = await collection.find_one({"ioc_value": ioc_data.get("ioc_value")})
            if existing:
                logger.debug(f"IOC already exists: {ioc_data.get('ioc_value')}")
                return False
            
            # Enrich the IOC using type-specific methods
            ioc_type = ioc_data.get("ioc_type")
            ioc_value = ioc_data.get("ioc_value")
            enriched_data = {}
            
            try:
                if ioc_type == "ipv4":
                    enriched_data = await enricher.enrich_ip(ioc_value)
                elif ioc_type in ["md5", "sha1", "sha256"]:
                    enriched_data = await enricher.enrich_hash(ioc_value)
                elif ioc_type == "domain":
                    enriched_data = await enricher.enrich_domain(ioc_value)
                elif ioc_type == "url":
                    enriched_data = await enricher.enrich_url(ioc_value)
                else:
                    # For unsupported types, use empty enrichment
                    enriched_data = {}
                    logger.debug(f"No enrichment available for IOC type: {ioc_type}")
            except Exception as e:
                logger.warning(f"Enrichment failed for {ioc_value}: {e}")
                enriched_data = {}
            
            # Merge IOC data with enrichment before severity scoring
            merged_data = {**ioc_data, **enriched_data}
            
            # Calculate severity score using merged data
            severity_info = severity_scorer.calculate_severity(merged_data)
            
            # Merge and normalize data, add correlation and metadata
            correlation_id = str(uuid.uuid4())

            # Determine IOC category for SIEM (filehash / ip / domain / url / other)
            category_map = {
                'md5': 'filehash', 'sha1': 'filehash', 'sha256': 'filehash',
                'ipv4': 'ip', 'domain': 'domain', 'url': 'url', 'cve': 'cve', 'email': 'email'
            }
            ioc_category = category_map.get(ioc_data.get('ioc_type'), 'other')

            # Ensure vt detection fields have consistent format
            vt_detections = merged_data.get('vt_detections')
            vt_rate = merged_data.get('vt_detection_rate')
            try:
                if vt_detections and isinstance(vt_detections, str) and '/' in vt_detections:
                    parts = vt_detections.split('/')
                    detected = int(parts[0])
                    total = int(parts[1]) if int(parts[1]) > 0 else 0
                    vt_rate = detected / total if total > 0 else 0.0
                elif isinstance(vt_detections, (list, tuple)) and len(vt_detections) == 2:
                    detected = int(vt_detections[0]); total = int(vt_detections[1])
                    vt_detections = f"{detected}/{total}"
                    vt_rate = detected / total if total > 0 else 0.0
                elif vt_rate is None:
                    vt_rate = 0.0
                    vt_detections = vt_detections or "0/0"
            except Exception:
                vt_rate = 0.0
                vt_detections = "0/0"

            # Populate abuse_score from sources if available
            abuse_score = merged_data.get('abuse_score')
            if not abuse_score:
                abuse_score = merged_data.get('sources', {}).get('abuseipdb', {}).get('abuse_confidence_score', None)

            # Threat actor metadata (prefer IOC-level, then pulse-level)
            threat_actor = merged_data.get('threat_actor') or ioc_data.get('threat_actor') or merged_data.get('pulse_author') or None

            final_ioc = {
                **ioc_data,
                **enriched_data,
                **severity_info,
                "correlation_id": correlation_id,
                "ioc_category": ioc_category,
                "abuse_score": abuse_score,
                "vt_detections": vt_detections,
                "vt_detection_rate": vt_rate,
                "threat_actor": threat_actor,
                "first_seen": datetime.utcnow(),
                "last_updated": datetime.utcnow(),
                "enrichment_status": "completed"
            }

            # Store in MongoDB
            await collection.insert_one(final_ioc)

            logger.debug(f"✅ Stored IOC: {ioc_data.get('ioc_value')} - {severity_info.get('severity')}")
            self.stats['iocs_stored'] += 1
            self.stats['iocs_enriched'] += 1

            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store IOC {ioc_data.get('ioc_value')}: {e}")
            self.stats['failed_stores'] += 1
            return False
    
    async def ingest_otx_pulses(self, limit: int = 50) -> int:
        """
        Fetch OTX threat pulses and store IOCs.
        
        Args:
            limit: Maximum number of pulses to fetch
            
        Returns:
            Number of IOCs stored
        """
        logger.info(f"📡 Fetching {limit} OTX pulses...")
        
        try:
            pulses = await threat_feeds.fetch_otx_pulses(limit=limit)
            self.stats['otx_pulses'] = len(pulses)
            logger.info(f"✅ Fetched {len(pulses)} OTX pulses")
            
            ioc_count = 0
            
            for pulse in pulses:
                pulse_name = pulse.get("name", "Unknown")
                indicators = pulse.get("indicators", [])
                
                logger.info(f"  Processing pulse: {pulse_name} ({len(indicators)} indicators)")
                
                for indicator in indicators:
                    ioc_type = indicator.get("type", "").lower()
                    ioc_value = indicator.get("indicator", "")
                    
                    if not ioc_value:
                        continue
                    
                    # Map OTX types to our IOC types
                    type_mapping = {
                        "ipv4": "ipv4",
                        "ipv6": "ipv4",
                        "domain": "domain",
                        "hostname": "domain",
                        "url": "url",
                        "filehash-md5": "md5",
                        "filehash-sha1": "sha1",
                        "filehash-sha256": "sha256",
                        "cve": "cve",
                        "email": "email"
                    }
                    
                    mapped_type = type_mapping.get(ioc_type)
                    if not mapped_type:
                        continue
                    
                    # Build IOC data
                    ioc_data = {
                        "ioc_value": ioc_value,
                        "ioc_type": mapped_type,
                        "source": "OTX",
                        "description": f"From OTX pulse: {pulse_name}",
                        "tags": pulse.get("tags", []),
                        "pulse_id": pulse.get("id"),
                        "pulse_name": pulse_name,
                        "threat_actor": pulse.get("author_name"),
                        "pulse_tlp": pulse.get("tlp"),
                        "context": indicator.get("description", "")
                    }
                    
                    # Store IOC
                    if await self.store_ioc(ioc_data):
                        ioc_count += 1
                
            logger.info(f"✅ Stored {ioc_count} new IOCs from OTX")
            return ioc_count
            
        except Exception as e:
            logger.error(f"❌ Failed to ingest OTX pulses: {e}")
            return 0
    
    async def ingest_urlhaus_urls(self, limit: int = 100) -> int:
        """
        Fetch URLhaus malware URLs and store IOCs.
        
        Args:
            limit: Maximum number of URLs to fetch
            
        Returns:
            Number of IOCs stored
        """
        logger.info(f"📡 Fetching {limit} URLhaus URLs...")
        
        try:
            urls = await threat_feeds.fetch_urlhaus_urls(limit=limit)
            self.stats['urlhaus_urls'] = len(urls)
            logger.info(f"✅ Fetched {len(urls)} URLhaus URLs")
            
            ioc_count = 0
            
            for url_data in urls:
                url = url_data.get("url", "")
                
                if not url:
                    continue
                
                # Extract host from URL
                host = ""
                if "://" in url:
                    host = url.split("://")[1].split("/")[0]
                
                # Store URL as IOC
                url_ioc = {
                    "ioc_value": url,
                    "ioc_type": "url",
                    "source": "URLhaus",
                    "description": f"URLhaus malware URL - Status: {url_data.get('url_status', 'unknown')}",
                    "threat_type": url_data.get("threat", "unknown"),
                    "tags": url_data.get("tags", []),
                    "urlhaus_status": url_data.get("url_status")
                }
                
                if await self.store_ioc(url_ioc):
                    ioc_count += 1
                
                # Store host as domain IOC
                if host and "." in host:
                    domain_ioc = {
                        "ioc_value": host,
                        "ioc_type": "domain",
                        "source": "URLhaus",
                        "description": f"Host from URLhaus malware URL",
                        "threat_type": url_data.get("threat", "unknown"),
                        "tags": url_data.get("tags", []),
                        "related_url": url
                    }

                    if await self.store_ioc(domain_ioc):
                        ioc_count += 1

            logger.info(f"✅ Stored {ioc_count} new IOCs from URLhaus URLs")
            return ioc_count

        except Exception as e:
            logger.error(f"❌ Failed to ingest URLhaus URLs: {e}")
            return 0
    
    async def ingest_urlhaus_payloads(self, limit: int = 100) -> int:
        """
        Fetch URLhaus malware payloads and store hash IOCs.
        
        Args:
            limit: Maximum number of payloads to fetch
            
        Returns:
            Number of IOCs stored
        """
        logger.info(f"📡 Fetching {limit} URLhaus payloads...")
        
        try:
            payloads = await threat_feeds.fetch_urlhaus_payloads(limit=limit)
            self.stats['urlhaus_payloads'] = len(payloads)
            logger.info(f"✅ Fetched {len(payloads)} URLhaus payloads")
            
            ioc_count = 0
            
            for payload in payloads:
                sha256 = payload.get("sha256_hash", "")
                md5 = payload.get("md5_hash", "")
                
                # Store SHA256
                if sha256:
                    sha256_ioc = {
                        "ioc_value": sha256,
                        "ioc_type": "sha256",
                        "source": "URLhaus",
                        "description": f"URLhaus malware payload - {payload.get('file_type', 'unknown')}",
                        "malware_family": payload.get("signature"),
                        "file_type": payload.get("file_type"),
                        "file_size": payload.get("file_size")
                    }
                    
                    if await self.store_ioc(sha256_ioc):
                        ioc_count += 1
                
                # Store MD5
                if md5:
                    md5_ioc = {
                        "ioc_value": md5,
                        "ioc_type": "md5",
                        "source": "URLhaus",
                        "description": f"URLhaus malware payload - {payload.get('file_type', 'unknown')}",
                        "malware_family": payload.get("signature"),
                        "file_type": payload.get("file_type"),
                        "file_size": payload.get("file_size")
                    }
                    
                    if await self.store_ioc(md5_ioc):
                        ioc_count += 1
            
            logger.info(f"✅ Stored {ioc_count} new IOCs from URLhaus payloads")
            return ioc_count
            
        except Exception as e:
            logger.error(f"❌ Failed to ingest URLhaus payloads: {e}")
            return 0
    
    async def run_full_ingestion(self):
        """
        Run complete ingestion cycle across all threat feeds.
        """
        logger.info("🚀 Starting full threat intelligence ingestion...")
        start_time = datetime.utcnow()
        
        try:
            # Connect to database
            await connect_db()
            
            # Fetch from all sources
            otx_count = await self.ingest_otx_pulses(limit=50)
            urlhaus_url_count = await self.ingest_urlhaus_urls(limit=100)
            urlhaus_payload_count = await self.ingest_urlhaus_payloads(limit=100)
            
            total_iocs = otx_count + urlhaus_url_count + urlhaus_payload_count
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 60)
            logger.info("📊 Ingestion Summary:")
            logger.info(f"  OTX Pulses: {self.stats['otx_pulses']}")
            logger.info(f"  URLhaus URLs: {self.stats['urlhaus_urls']}")
            logger.info(f"  URLhaus Payloads: {self.stats['urlhaus_payloads']}")
            logger.info(f"  Total IOCs Stored: {self.stats['iocs_stored']}")
            logger.info(f"  IOCs Enriched: {self.stats['iocs_enriched']}")
            logger.info(f"  Failed Stores: {self.stats['failed_stores']}")
            logger.info(f"  Duration: {duration:.2f} seconds")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Ingestion failed: {e}")
            raise
        finally:
            await disconnect_db()


async def main():
    """Entry point for direct ingestion service."""
    logger.info("🔧 SecInt v2 - Direct Threat Ingestion Service (Localhost)")
    
    service = DirectThreatIngestionService()
    await service.run_full_ingestion()


if __name__ == "__main__":
    asyncio.run(main())
