"""
enricher.py - IOC enrichment using threat intelligence APIs
Enriches IOCs with reputation data from VirusTotal and AbuseIPDB
"""
import asyncio
from typing import Dict, Optional, List
from datetime import datetime
import logging

from services.threat_feeds import threat_feeds

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IOCEnricher:
    """Enrich IOCs with threat intelligence data"""
    
    def __init__(self):
        """Initialize enricher with threat feed aggregator"""
        self.feeds = threat_feeds
        self._rate_limit_delay = 0.5  # Delay between API calls (seconds)
    
    async def enrich_ip(self, ip: str) -> Dict:
        """
        Enrich IP address with reputation data
        
        Args:
            ip: IP address to enrich
            
        Returns:
            Enriched IP data dictionary
        """
        enriched = {
            'ioc_value': ip,
            'ioc_type': 'ipv4',
            'enrichment_timestamp': datetime.utcnow(),
            'sources': {}
        }
        
        # Fetch from both AbuseIPDB and VirusTotal concurrently
        results = await asyncio.gather(
            self.feeds.check_ip_reputation(ip),
            self.feeds.check_ip_virustotal(ip),
            return_exceptions=True
        )
        
        # AbuseIPDB data
        if results[0] and not isinstance(results[0], Exception):
            abuseipdb_data = results[0]
            enriched['sources']['abuseipdb'] = {
                'abuse_confidence_score': abuseipdb_data.get('abuseConfidenceScore', 0),
                'total_reports': abuseipdb_data.get('totalReports', 0),
                'country_code': abuseipdb_data.get('countryCode'),
                'isp': abuseipdb_data.get('isp'),
                'domain': abuseipdb_data.get('domain'),
                'is_whitelisted': abuseipdb_data.get('isWhitelisted', False),
            }
            enriched['abuse_score'] = abuseipdb_data.get('abuseConfidenceScore', 0)
        
        # VirusTotal data
        if results[1] and not isinstance(results[1], Exception):
            vt_data = results[1]
            attributes = vt_data.get('attributes', {})
            last_analysis = attributes.get('last_analysis_stats', {})
            
            enriched['sources']['virustotal'] = {
                'malicious': last_analysis.get('malicious', 0),
                'suspicious': last_analysis.get('suspicious', 0),
                'harmless': last_analysis.get('harmless', 0),
                'undetected': last_analysis.get('undetected', 0),
                'reputation': attributes.get('reputation', 0),
                'country': attributes.get('country'),
                'as_owner': attributes.get('as_owner'),
            }
            
            # Calculate detection rate
            total = sum(last_analysis.values())
            if total > 0:
                detected = last_analysis.get('malicious', 0) + last_analysis.get('suspicious', 0)
                enriched['vt_detection_rate'] = detected / total
                enriched['vt_detections'] = f"{detected}/{total}"
        
        return enriched
    
    async def enrich_hash(self, file_hash: str, hash_type: str = 'sha256') -> Dict:
        """
        Enrich file hash with malware analysis data
        
        Args:
            file_hash: MD5, SHA1, or SHA256 hash
            hash_type: Type of hash (md5, sha1, sha256)
            
        Returns:
            Enriched hash data dictionary
        """
        enriched = {
            'ioc_value': file_hash,
            'ioc_type': hash_type,
            'enrichment_timestamp': datetime.utcnow(),
            'sources': {}
        }
        
        # Check VirusTotal
        vt_data = await self.feeds.check_file_hash(file_hash)
        
        if vt_data:
            attributes = vt_data.get('attributes', {})
            last_analysis = attributes.get('last_analysis_stats', {})
            
            enriched['sources']['virustotal'] = {
                'malicious': last_analysis.get('malicious', 0),
                'suspicious': last_analysis.get('suspicious', 0),
                'harmless': last_analysis.get('harmless', 0),
                'undetected': last_analysis.get('undetected', 0),
                'file_type': attributes.get('type_description'),
                'file_size': attributes.get('size'),
                'first_submission_date': attributes.get('first_submission_date'),
                'last_analysis_date': attributes.get('last_analysis_date'),
                'reputation': attributes.get('reputation', 0),
            }
            
            # Extract malware family names
            popular_threat_names = attributes.get('popular_threat_classification', {})
            if popular_threat_names:
                suggested_threat = popular_threat_names.get('suggested_threat_label')
                if suggested_threat:
                    enriched['malware_family'] = suggested_threat
            
            # Calculate detection rate
            total = sum(last_analysis.values())
            if total > 0:
                detected = last_analysis.get('malicious', 0) + last_analysis.get('suspicious', 0)
                enriched['vt_detection_rate'] = detected / total
                enriched['vt_detections'] = f"{detected}/{total}"
        
        return enriched
    
    async def enrich_domain(self, domain: str) -> Dict:
        """
        Enrich domain with threat intelligence
        
        Args:
            domain: Domain name to enrich
            
        Returns:
            Enriched domain data dictionary
        """
        enriched = {
            'ioc_value': domain,
            'ioc_type': 'domain',
            'enrichment_timestamp': datetime.utcnow(),
            'sources': {}
        }
        
        # For now, just basic structure
        # Can add domain-specific APIs later
        return enriched
    
    async def enrich_url(self, url: str) -> Dict:
        """
        Enrich URL with threat intelligence
        
        Args:
            url: URL to enrich
            
        Returns:
            Enriched URL data dictionary
        """
        enriched = {
            'ioc_value': url,
            'ioc_type': 'url',
            'enrichment_timestamp': datetime.utcnow(),
            'sources': {}
        }
        
        # URLhaus data is already enriched from the feed
        return enriched
    
    async def enrich_iocs(self, iocs: Dict[str, List[str]]) -> List[Dict]:
        """
        Enrich multiple IOCs of different types
        
        Args:
            iocs: Dictionary of IOC type -> list of IOC values
            
        Returns:
            List of enriched IOC dictionaries
        """
        enriched_iocs = []
        
        # Process IPs
        if 'ipv4' in iocs:
            for ip in iocs['ipv4'][:50]:  # Limit to avoid rate limits
                enriched = await self.enrich_ip(ip)
                enriched_iocs.append(enriched)
                await asyncio.sleep(self._rate_limit_delay)
        
        # Process hashes
        for hash_type in ['md5', 'sha1', 'sha256']:
            if hash_type in iocs:
                for file_hash in iocs[hash_type][:20]:  # Limit for VT quota
                    enriched = await self.enrich_hash(file_hash, hash_type)
                    enriched_iocs.append(enriched)
                    await asyncio.sleep(self._rate_limit_delay)
        
        # Process domains
        if 'domain' in iocs:
            for domain in iocs['domain'][:30]:
                enriched = await self.enrich_domain(domain)
                enriched_iocs.append(enriched)
        
        # Process URLs
        if 'url' in iocs:
            for url in iocs['url'][:30]:
                enriched = await self.enrich_url(url)
                enriched_iocs.append(enriched)
        
        logger.info(f"✅ Enriched {len(enriched_iocs)} IOCs")
        return enriched_iocs
    
    async def batch_enrich(self, ioc_list: List[Dict]) -> List[Dict]:
        """
        Enrich a batch of IOCs (already structured)
        
        Args:
            ioc_list: List of IOC dictionaries with 'value' and 'type'
            
        Returns:
            List of enriched IOCs
        """
        enriched = []
        
        for ioc in ioc_list:
            ioc_type = ioc.get('ioc_type', ioc.get('type'))
            ioc_value = ioc.get('ioc_value', ioc.get('value'))
            
            if not ioc_type or not ioc_value:
                continue
            
            if ioc_type == 'ipv4':
                enriched_data = await self.enrich_ip(ioc_value)
            elif ioc_type in ['md5', 'sha1', 'sha256']:
                enriched_data = await self.enrich_hash(ioc_value, ioc_type)
            elif ioc_type == 'domain':
                enriched_data = await self.enrich_domain(ioc_value)
            elif ioc_type == 'url':
                enriched_data = await self.enrich_url(ioc_value)
            else:
                enriched_data = {
                    'ioc_value': ioc_value,
                    'ioc_type': ioc_type,
                    'enrichment_timestamp': datetime.utcnow(),
                    'sources': {}
                }
            
            # Merge with original IOC data
            enriched_data.update(ioc)
            enriched.append(enriched_data)
            
            await asyncio.sleep(self._rate_limit_delay)
        
        return enriched


# Global instance
ioc_enricher = IOCEnricher()
enricher = ioc_enricher  # Alias for compatibility
