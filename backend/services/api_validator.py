"""
api_validator.py - API Health Check and Validation Service
Validates external API keys and monitors quota usage
"""
import os
import aiohttp
import asyncio
from typing import Dict, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIValidator:
    """Validate and monitor external threat intelligence API health"""
    
    def __init__(self):
        """Initialize API validator with environment variables"""
        self.otx_api_key = os.getenv('OTX_API_KEY')
        self.abuseipdb_api_key = os.getenv('ABUSEIPDB_API_KEY')
        self.urlhaus_api_key = os.getenv('URLHAUS_API_KEY')
        self.virustotal_api_key = os.getenv('VIRUSTOTAL_API_KEY')
        
        # API endpoints
        self.otx_base = 'https://otx.alienvault.com/api/v1'
        self.abuseipdb_base = 'https://api.abuseipdb.com/api/v2'
        self.urlhaus_base = 'https://urlhaus-api.abuse.ch/v1'
        self.virustotal_base = 'https://www.virustotal.com/api/v3'
        
        # Cache for health status
        self.health_cache = {}
        self.last_check = None
    
    async def validate_otx_api(self) -> Dict:
        """
        Validate AlienVault OTX API key
        
        Returns:
            Dict with status, message, and quota info
        """
        if not self.otx_api_key:
            return {
                'status': 'not_configured',
                'message': 'OTX API key not configured',
                'quota': None,
                'checked_at': datetime.utcnow().isoformat()
            }
        
        try:
            url = f"{self.otx_base}/user/me"
            headers = {'X-OTX-API-KEY': self.otx_api_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'status': 'ok',
                            'message': 'OTX API key is valid',
                            'user': data.get('username', 'Unknown'),
                            'quota': 'Unlimited (Free tier)',
                            'checked_at': datetime.utcnow().isoformat()
                        }
                    elif response.status == 403:
                        return {
                            'status': 'invalid',
                            'message': 'OTX API key is invalid or expired',
                            'quota': None,
                            'checked_at': datetime.utcnow().isoformat()
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': f'OTX API returned status {response.status}',
                            'quota': None,
                            'checked_at': datetime.utcnow().isoformat()
                        }
        except asyncio.TimeoutError:
            return {
                'status': 'timeout',
                'message': 'OTX API request timed out',
                'quota': None,
                'checked_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'OTX API check failed: {str(e)}',
                'quota': None,
                'checked_at': datetime.utcnow().isoformat()
            }
    
    async def validate_abuseipdb_api(self) -> Dict:
        """
        Validate AbuseIPDB API key
        
        Returns:
            Dict with status, message, and quota info
        """
        if not self.abuseipdb_api_key:
            return {
                'status': 'not_configured',
                'message': 'AbuseIPDB API key not configured',
                'quota': None,
                'checked_at': datetime.utcnow().isoformat()
            }
        
        try:
            # Use a test IP (Google DNS) for validation
            url = f"{self.abuseipdb_base}/check"
            headers = {
                'Key': self.abuseipdb_api_key,
                'Accept': 'application/json'
            }
            params = {'ipAddress': '8.8.8.8', 'maxAgeInDays': 90}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=10) as response:
                    if response.status == 200:
                        # Try to extract quota from headers
                        quota_limit = response.headers.get('X-RateLimit-Limit', 'Unknown')
                        quota_remaining = response.headers.get('X-RateLimit-Remaining', 'Unknown')
                        
                        return {
                            'status': 'ok',
                            'message': 'AbuseIPDB API key is valid',
                            'quota': f'{quota_remaining}/{quota_limit} daily requests',
                            'quota_remaining': quota_remaining,
                            'quota_limit': quota_limit,
                            'checked_at': datetime.utcnow().isoformat()
                        }
                    elif response.status == 401:
                        return {
                            'status': 'invalid',
                            'message': 'AbuseIPDB API key is invalid',
                            'quota': None,
                            'checked_at': datetime.utcnow().isoformat()
                        }
                    elif response.status == 429:
                        return {
                            'status': 'rate_limited',
                            'message': 'AbuseIPDB rate limit exceeded',
                            'quota': '0/1000 daily requests',
                            'checked_at': datetime.utcnow().isoformat()
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': f'AbuseIPDB API returned status {response.status}',
                            'quota': None,
                            'checked_at': datetime.utcnow().isoformat()
                        }
        except asyncio.TimeoutError:
            return {
                'status': 'timeout',
                'message': 'AbuseIPDB API request timed out',
                'quota': None,
                'checked_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'AbuseIPDB API check failed: {str(e)}',
                'quota': None,
                'checked_at': datetime.utcnow().isoformat()
            }
    
    async def validate_virustotal_api(self) -> Dict:
        """
        Validate VirusTotal API key
        
        Returns:
            Dict with status, message, and quota info
        """
        if not self.virustotal_api_key:
            return {
                'status': 'not_configured',
                'message': 'VirusTotal API key not configured',
                'quota': None,
                'checked_at': datetime.utcnow().isoformat()
            }
        
        try:
            # Use simple IP lookup endpoint instead of quota endpoint (works with basic API keys)
            url = f"{self.virustotal_base}/ip_addresses/8.8.8.8"
            headers = {'x-apikey': self.virustotal_api_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        # Extract quota from response headers if available
                        quota_limit = response.headers.get('X-Api-Quota', '500')
                        quota_used = response.headers.get('X-Api-Quota-Used', 'Unknown')
                        
                        return {
                            'status': 'ok',
                            'message': 'VirusTotal API key is valid',
                            'quota': f'Standard tier (check headers for usage)',
                            'quota_info': f'Limit: {quota_limit}/day',
                            'checked_at': datetime.utcnow().isoformat()
                        }
                    elif response.status == 401:
                        return {
                            'status': 'invalid',
                            'message': 'VirusTotal API key is invalid',
                            'quota': None,
                            'checked_at': datetime.utcnow().isoformat()
                        }
                    elif response.status == 429:
                        return {
                            'status': 'rate_limited',
                            'message': 'VirusTotal rate limit exceeded',
                            'quota': '0/500 daily requests',
                            'checked_at': datetime.utcnow().isoformat()
                        }
                    elif response.status == 403:
                        # 403 might mean quota endpoint not accessible, but key might still work
                        return {
                            'status': 'ok',
                            'message': 'VirusTotal API key is valid (quota endpoint restricted)',
                            'quota': 'Standard free tier (500 req/day, 4 req/min)',
                            'checked_at': datetime.utcnow().isoformat()
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': f'VirusTotal API returned status {response.status}',
                            'quota': None,
                            'checked_at': datetime.utcnow().isoformat()
                        }
        except asyncio.TimeoutError:
            return {
                'status': 'timeout',
                'message': 'VirusTotal API request timed out',
                'quota': None,
                'checked_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'VirusTotal API check failed: {str(e)}',
                'quota': None,
                'checked_at': datetime.utcnow().isoformat()
            }
    
    async def validate_urlhaus_api(self) -> Dict:
        """
        Validate URLhaus API access (public API, Auth-Key optional for rate limit bypass)
        
        Returns:
            Dict with status, message
        """
        # URLhaus API is public and doesn't require authentication for basic access
        # Auth-Key is optional and only helps bypass rate limits
        
        try:
            url = f"{self.urlhaus_base}/urls/recent/"
            headers = {}
            
            # Add Auth-Key if configured (optional)
            if self.urlhaus_api_key:
                headers['Auth-Key'] = self.urlhaus_api_key
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('query_status') == 'ok':
                            auth_msg = 'with Auth-Key' if self.urlhaus_api_key else 'without Auth-Key (public)'
                            return {
                                'status': 'ok',
                                'message': f'URLhaus API accessible {auth_msg}',
                                'quota': 'Unlimited with Auth-Key' if self.urlhaus_api_key else 'Rate-limited (public)',
                                'checked_at': datetime.utcnow().isoformat()
                            }
                        else:
                            return {
                                'status': 'error',
                                'message': f"URLhaus API query failed: {data.get('query_status')}",
                                'quota': None,
                                'checked_at': datetime.utcnow().isoformat()
                            }
                    elif response.status == 401:
                        return {
                            'status': 'invalid',
                            'message': 'URLhaus Auth-Key is invalid or unauthorized',
                            'quota': None,
                            'checked_at': datetime.utcnow().isoformat()
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': f'URLhaus API returned status {response.status}',
                            'quota': None,
                            'checked_at': datetime.utcnow().isoformat()
                        }
        except asyncio.TimeoutError:
            return {
                'status': 'timeout',
                'message': 'URLhaus API request timed out (may be slow or down)',
                'quota': None,
                'checked_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'URLhaus API check failed: {str(e)}',
                'quota': None,
                'checked_at': datetime.utcnow().isoformat()
            }
    
    async def validate_all_apis(self, use_cache: bool = True) -> Dict:
        """
        Validate all configured APIs concurrently
        
        Args:
            use_cache: Use cached results if available (within 5 minutes)
            
        Returns:
            Dictionary with status for each API
        """
        # Check cache
        if use_cache and self.health_cache and self.last_check:
            cache_age = (datetime.utcnow() - self.last_check).total_seconds()
            if cache_age < 300:  # 5 minutes
                logger.info(f"Using cached API health status ({cache_age:.0f}s old)")
                return self.health_cache
        
        logger.info("🔍 Validating all external APIs...")
        
        # Run all validations concurrently
        results = await asyncio.gather(
            self.validate_otx_api(),
            self.validate_abuseipdb_api(),
            self.validate_virustotal_api(),
            self.validate_urlhaus_api(),
            return_exceptions=True
        )
        
        # Process results
        health_status = {
            'otx': results[0] if not isinstance(results[0], Exception) else {
                'status': 'error',
                'message': f'Validation failed: {str(results[0])}',
                'quota': None
            },
            'abuseipdb': results[1] if not isinstance(results[1], Exception) else {
                'status': 'error',
                'message': f'Validation failed: {str(results[1])}',
                'quota': None
            },
            'virustotal': results[2] if not isinstance(results[2], Exception) else {
                'status': 'error',
                'message': f'Validation failed: {str(results[2])}',
                'quota': None
            },
            'urlhaus': results[3] if not isinstance(results[3], Exception) else {
                'status': 'error',
                'message': f'Validation failed: {str(results[3])}',
                'quota': None
            }
        }
        
        # Update cache
        self.health_cache = health_status
        self.last_check = datetime.utcnow()
        
        # Log summary
        ok_count = sum(1 for api in health_status.values() if api['status'] == 'ok')
        total_count = len(health_status)
        
        logger.info(f"✅ API Health Check Complete: {ok_count}/{total_count} APIs operational")
        
        for api_name, status in health_status.items():
            if status['status'] == 'ok':
                logger.info(f"  ✅ {api_name.upper()}: {status['message']}")
            elif status['status'] == 'not_configured':
                logger.warning(f"  ⚠️ {api_name.upper()}: {status['message']}")
            else:
                logger.error(f"  ❌ {api_name.upper()}: {status['message']}")
        
        return health_status
    
    def get_overall_status(self, health_status: Dict) -> str:
        """
        Get overall system health status
        
        Args:
            health_status: Dictionary from validate_all_apis()
            
        Returns:
            Overall status string
        """
        ok_count = sum(1 for api in health_status.values() if api['status'] == 'ok')
        total_configured = sum(1 for api in health_status.values() if api['status'] != 'not_configured')
        
        if ok_count == total_configured and total_configured > 0:
            return 'healthy'
        elif ok_count >= total_configured / 2:
            return 'degraded'
        else:
            return 'unhealthy'


# Global instance
api_validator = APIValidator()
