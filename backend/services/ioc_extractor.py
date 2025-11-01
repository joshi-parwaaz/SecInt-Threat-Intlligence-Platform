"""
ioc_extractor.py - Rule-based IOC extraction using regex patterns
Extracts IPs, domains, URLs, file hashes, and CVE numbers from threat data
"""
import re
from typing import List, Dict, Set
from enum import Enum

class IOCType(str, Enum):
    IPV4 = "ipv4"
    DOMAIN = "domain"
    URL = "url"
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    CVE = "cve"
    EMAIL = "email"

class IOCExtractor:
    """Extract Indicators of Compromise from text using regex patterns"""
    
    # Regex patterns for IOC extraction
    PATTERNS = {
        IOCType.IPV4: r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        IOCType.DOMAIN: r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b',
        IOCType.URL: r'https?://[^\s<>"{}|\\^`\[\]]+',
        IOCType.MD5: r'\b[a-fA-F0-9]{32}\b',
        IOCType.SHA1: r'\b[a-fA-F0-9]{40}\b',
        IOCType.SHA256: r'\b[a-fA-F0-9]{64}\b',
        IOCType.CVE: r'CVE-\d{4}-\d{4,7}',
        IOCType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    }
    
    # Private IP ranges to filter out
    PRIVATE_IP_PATTERNS = [
        r'^127\.',           # Loopback
        r'^10\.',            # Class A private
        r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',  # Class B private
        r'^192\.168\.',      # Class C private
        r'^0\.',             # Invalid
        r'^169\.254\.',      # Link-local
        r'^224\.',           # Multicast
        r'^255\.',           # Broadcast
    ]
    
    # Common non-threatening domains to filter
    BENIGN_DOMAINS = {
        'localhost', 'example.com', 'example.org', 'example.net',
        'test.com', 'domain.com', 'google.com', 'microsoft.com',
        'w3.org', 'ietf.org', 'github.com', 'stackoverflow.com'
    }
    
    def __init__(self):
        """Initialize compiled regex patterns for performance"""
        self.compiled_patterns = {
            ioc_type: re.compile(pattern, re.IGNORECASE)
            for ioc_type, pattern in self.PATTERNS.items()
        }
        self.private_ip_compiled = [
            re.compile(pattern) for pattern in self.PRIVATE_IP_PATTERNS
        ]
    
    def extract_all(self, text: str) -> Dict[str, List[str]]:
        """
        Extract all IOC types from text
        
        Args:
            text: Input text to extract IOCs from
            
        Returns:
            Dictionary with IOC types as keys and lists of unique IOCs as values
        """
        if not text:
            return {}
        
        results = {}
        
        for ioc_type, pattern in self.compiled_patterns.items():
            matches = pattern.findall(text)
            if matches:
                # Deduplicate and validate
                unique_iocs = self._validate_iocs(ioc_type, set(matches))
                if unique_iocs:
                    results[ioc_type.value] = sorted(list(unique_iocs))
        
        return results
    
    def extract_by_type(self, text: str, ioc_type: IOCType) -> List[str]:
        """
        Extract specific IOC type from text
        
        Args:
            text: Input text
            ioc_type: Type of IOC to extract
            
        Returns:
            List of unique validated IOCs
        """
        if not text or ioc_type not in self.compiled_patterns:
            return []
        
        matches = self.compiled_patterns[ioc_type].findall(text)
        return sorted(list(self._validate_iocs(ioc_type, set(matches))))
    
    def _validate_iocs(self, ioc_type: IOCType, iocs: Set[str]) -> Set[str]:
        """
        Validate and filter IOCs based on type-specific rules
        
        Args:
            ioc_type: Type of IOC
            iocs: Set of IOCs to validate
            
        Returns:
            Filtered set of valid IOCs
        """
        if not iocs:
            return set()
        
        if ioc_type == IOCType.IPV4:
            return self._validate_ips(iocs)
        elif ioc_type == IOCType.DOMAIN:
            return self._validate_domains(iocs)
        elif ioc_type in [IOCType.MD5, IOCType.SHA1, IOCType.SHA256]:
            return self._validate_hashes(iocs)
        elif ioc_type == IOCType.URL:
            return self._validate_urls(iocs)
        else:
            return iocs  # CVE and email don't need special validation
    
    def _validate_ips(self, ips: Set[str]) -> Set[str]:
        """Filter out private/invalid IP addresses"""
        valid_ips = set()
        
        for ip in ips:
            # Check if IP is private
            is_private = any(
                pattern.match(ip) for pattern in self.private_ip_compiled
            )
            
            if not is_private:
                # Validate octets are in range
                try:
                    octets = [int(x) for x in ip.split('.')]
                    if all(0 <= octet <= 255 for octet in octets):
                        valid_ips.add(ip)
                except ValueError:
                    continue
        
        return valid_ips
    
    def _validate_domains(self, domains: Set[str]) -> Set[str]:
        """Filter out benign/example domains"""
        valid_domains = set()
        
        for domain in domains:
            domain_lower = domain.lower()
            
            # Skip benign domains
            if domain_lower in self.BENIGN_DOMAINS:
                continue
            
            # Skip domains that look like file extensions or single words
            if '.' not in domain or len(domain.split('.')) < 2:
                continue
            
            # Skip numeric-only domains
            if domain.replace('.', '').isdigit():
                continue
            
            valid_domains.add(domain_lower)
        
        return valid_domains
    
    def _validate_hashes(self, hashes: Set[str]) -> Set[str]:
        """Validate hash format (hex characters only)"""
        return {h.lower() for h in hashes if h.isalnum()}
    
    def _validate_urls(self, urls: Set[str]) -> Set[str]:
        """Basic URL validation"""
        valid_urls = set()
        
        for url in urls:
            # Skip URLs with benign domains
            url_lower = url.lower()
            if any(domain in url_lower for domain in self.BENIGN_DOMAINS):
                continue
            
            # Basic sanity check
            if len(url) > 10 and '.' in url:
                valid_urls.add(url)
        
        return valid_urls
    
    def count_iocs(self, text: str) -> Dict[str, int]:
        """
        Count IOCs by type without extracting them
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with IOC types and counts
        """
        results = self.extract_all(text)
        return {
            ioc_type: len(iocs) 
            for ioc_type, iocs in results.items()
        }


# Global instance for reuse
ioc_extractor = IOCExtractor()


def extract_iocs(text: str) -> Dict[str, List[str]]:
    """
    Convenience function to extract all IOCs from text
    
    Args:
        text: Input text
        
    Returns:
        Dictionary of IOC types and values
    """
    return ioc_extractor.extract_all(text)
