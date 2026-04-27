"""
threat_feeds.py - Real-time threat intelligence feed aggregator
Pulls live IOCs from AlienVault OTX, AbuseIPDB, URLhaus, and VirusTotal
"""
import os
import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreatFeedAggregator:
    """Aggregate threat intelligence from multiple sources"""
    
    def __init__(self):
        """Initialize with API keys from environment"""
        self.otx_api_key = os.getenv('OTX_API_KEY')
        self.abuseipdb_api_key = os.getenv('ABUSEIPDB_API_KEY')
        self.urlhaus_api_key = os.getenv('URLHAUS_API_KEY')
        self.virustotal_api_key = os.getenv('VIRUSTOTAL_API_KEY')
        
        # API endpoints
        self.otx_base = 'https://otx.alienvault.com/api/v1'
        self.abuseipdb_base = 'https://api.abuseipdb.com/api/v2'
        self.urlhaus_base = 'https://urlhaus-api.abuse.ch/v1'
        self.virustotal_base = 'https://www.virustotal.com/api/v3'
    
    async def fetch_otx_pulses(self, limit: int = 50) -> List[Dict]:
        """
        Fetch threat pulses from AlienVault OTX
        
        Args:
            limit: Maximum number of pulses to fetch
            
        Returns:
            List of threat pulse dictionaries
        """
        if not self.otx_api_key:
            logger.warning("OTX API key not configured")
            return []
        
        url = f"{self.otx_base}/pulses/subscribed"
        headers = {'X-OTX-API-KEY': self.otx_api_key}
        params = {'limit': limit, 'page': 1}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        pulses = data.get('results', [])
                        logger.info(f"✅ Fetched {len(pulses)} threat pulses from OTX")
                        return pulses
                    else:
                        logger.error(f"❌ OTX API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ OTX fetch failed: {e}")
            return []
    
    async def fetch_urlhaus_urls(self, limit: int = 100) -> List[Dict]:
        """
        Fetch recent malware URLs from URLhaus
        
        Args:
            limit: Maximum number of URLs to fetch (max 1000)
            
        Returns:
            List of malware URL dictionaries
        """
        # URLhaus requires Auth-Key header
        url = f"{self.urlhaus_base}/urls/recent/"
        headers = {}
        if self.urlhaus_api_key:
            headers['Auth-Key'] = self.urlhaus_api_key
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('query_status') == 'ok':
                            urls = data.get('urls', [])[:limit]
                            logger.info(f"✅ Fetched {len(urls)} malware URLs from URLhaus")
                            return urls
                        else:
                            logger.error(f"❌ URLhaus query failed: {data.get('query_status')}")
                            return []
                    else:
                        logger.error(f"❌ URLhaus API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ URLhaus fetch failed: {e}")
            return []
    
    async def fetch_urlhaus_payloads(self, limit: int = 100) -> List[Dict]:
        """
        Fetch recent malware payloads (file hashes) from URLhaus
        
        Args:
            limit: Maximum number of payloads to fetch
            
        Returns:
            List of payload dictionaries with hashes
        """
        url = f"{self.urlhaus_base}/payloads/recent/"
        headers = {}
        if self.urlhaus_api_key:
            headers['Auth-Key'] = self.urlhaus_api_key
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('query_status') == 'ok':
                            payloads = data.get('payloads', [])[:limit]
                            logger.info(f"✅ Fetched {len(payloads)} malware payloads from URLhaus")
                            return payloads
                        else:
                            logger.error(f"❌ URLhaus payloads query failed: {data.get('query_status')}")
                            return []
                    else:
                        logger.error(f"❌ URLhaus API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ URLhaus payloads fetch failed: {e}")
            return []
    
    async def check_ip_reputation(self, ip: str) -> Optional[Dict]:
        """
        Check IP reputation on AbuseIPDB
        
        Args:
            ip: IP address to check
            
        Returns:
            Reputation data dictionary or None
        """
        if not self.abuseipdb_api_key:
            logger.warning("AbuseIPDB API key not configured")
            return None
        
        url = f"{self.abuseipdb_base}/check"
        headers = {
            'Key': self.abuseipdb_api_key,
            'Accept': 'application/json'
        }
        params = {'ipAddress': ip, 'maxAgeInDays': 90}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {})
                    elif response.status == 429:
                        logger.warning("⚠️ AbuseIPDB rate limit reached")
                        return None
                    else:
                        logger.error(f"❌ AbuseIPDB API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"❌ AbuseIPDB check failed for {ip}: {e}")
            return None
    
    async def check_file_hash(self, file_hash: str) -> Optional[Dict]:
        """
        Check file hash reputation on VirusTotal
        
        Args:
            file_hash: MD5, SHA1, or SHA256 hash
            
        Returns:
            VirusTotal analysis data or None
        """
        if not self.virustotal_api_key:
            logger.warning("VirusTotal API key not configured")
            return None
        
        url = f"{self.virustotal_base}/files/{file_hash}"
        headers = {'x-apikey': self.virustotal_api_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {})
                    elif response.status == 404:
                        logger.debug(f"Hash not found in VirusTotal: {file_hash[:8]}...")
                        return None
                    elif response.status == 429:
                        logger.warning("⚠️ VirusTotal rate limit reached")
                        return None
                    else:
                        logger.error(f"❌ VirusTotal API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"❌ VirusTotal check failed for {file_hash[:8]}...: {e}")
            return None
    
    async def check_ip_virustotal(self, ip: str) -> Optional[Dict]:
        """
        Check IP address on VirusTotal
        
        Args:
            ip: IP address to check
            
        Returns:
            VirusTotal IP data or None
        """
        if not self.virustotal_api_key:
            return None
        
        url = f"{self.virustotal_base}/ip_addresses/{ip}"
        headers = {'x-apikey': self.virustotal_api_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {})
                    elif response.status == 429:
                        logger.warning("⚠️ VirusTotal rate limit reached")
                        return None
                    else:
                        return None
        except Exception as e:
            logger.error(f"❌ VirusTotal IP check failed for {ip}: {e}")
            return None
    
    async def fetch_all_feeds(self) -> Dict[str, List[Dict]]:
        """
        Fetch data from all threat feeds concurrently
        
        Returns:
            Dictionary with feed names and their data
        """
        logger.info("🔄 Fetching threat intelligence from all sources...")
        
        # Fetch all feeds concurrently
        results = await asyncio.gather(
            self.fetch_otx_pulses(limit=50),
            self.fetch_urlhaus_urls(limit=100),
            self.fetch_urlhaus_payloads(limit=100),
            return_exceptions=True
        )
        
        # Handle results
        feeds = {
            'otx_pulses': results[0] if not isinstance(results[0], Exception) else [],
            'urlhaus_urls': results[1] if not isinstance(results[1], Exception) else [],
            'urlhaus_payloads': results[2] if not isinstance(results[2], Exception) else [],
        }
        
        total_items = sum(len(items) for items in feeds.values())
        logger.info(f"✅ Fetched {total_items} total threat indicators from all sources")
        
        return feeds


# Global instance
threat_feeds = ThreatFeedAggregator()
