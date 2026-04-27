"""
severity_scorer.py - Rule-based severity scoring for IOCs
Assigns CRITICAL/HIGH/MEDIUM/LOW severity based on threat intelligence
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"

class SeverityScorer:
    """Calculate threat severity based on enrichment data and context"""
    
    # Known critical malware families
    CRITICAL_MALWARE_FAMILIES = {
        'emotet', 'trickbot', 'ryuk', 'ransomware', 'wannacry',
        'lockbit', 'conti', 'revil', 'sodinokibi', 'blackmatter',
        'darkside', 'ragnar', 'maze', 'egregor', 'netwalker',
        'dridex', 'qbot', 'qakbot', 'icedid', 'cobalt strike',
        'metasploit', 'mimikatz', 'lazarus', 'apt28', 'apt29'
    }
    
    # High-risk malware families
    HIGH_RISK_MALWARE_FAMILIES = {
        'gozi', 'ursnif', 'zeus', 'formbook', 'agent tesla',
        'lokibot', 'njrat', 'remcos', 'nanocore', 'asyncrat',
        'redline', 'vidar', 'raccoon', 'azorult', 'baldr',
        'netwire', 'warzone', 'darkcomet', 'poison ivy'
    }
    
    # Critical threat types
    CRITICAL_THREAT_TYPES = {
        'ransomware', 'c2', 'command and control', 'botnet',
        'apt', 'advanced persistent threat', '0day', 'zero-day',
        'exploit kit', 'cryptominer'
    }
    
    def __init__(self):
        """Initialize severity scorer"""
        pass
    
    def calculate_severity(self, ioc_data: Dict) -> Dict:
        """
        Calculate severity score and level for an IOC
        
        Args:
            ioc_data: Enriched IOC dictionary
            
        Returns:
            IOC data with added 'severity' and 'severity_score' fields
        """
        score = 0
        reasons = []
        
        ioc_type = ioc_data.get('ioc_type', 'unknown')
        sources = ioc_data.get('sources', {})
        
        # === VirusTotal Detection Rate ===
        vt_detection_rate = ioc_data.get('vt_detection_rate', 0)
        if vt_detection_rate > 0.8:
            score += 50
            reasons.append(f"VT detection: {ioc_data.get('vt_detections', 'N/A')} (>80%)")
        elif vt_detection_rate > 0.5:
            score += 30
            reasons.append(f"VT detection: {ioc_data.get('vt_detections', 'N/A')} (>50%)")
        elif vt_detection_rate > 0.2:
            score += 15
            reasons.append(f"VT detection: {ioc_data.get('vt_detections', 'N/A')} (>20%)")
        
        # === Malware Family ===
        malware_family = ioc_data.get('malware_family', '').lower()
        if malware_family:
            if any(critical in malware_family for critical in self.CRITICAL_MALWARE_FAMILIES):
                score += 40
                reasons.append(f"Critical malware: {malware_family}")
            elif any(high_risk in malware_family for high_risk in self.HIGH_RISK_MALWARE_FAMILIES):
                score += 25
                reasons.append(f"High-risk malware: {malware_family}")
            else:
                score += 10
                reasons.append(f"Known malware: {malware_family}")
        
        # === AbuseIPDB Score ===
        if ioc_type == 'ipv4' and 'abuseipdb' in sources:
            abuse_score = sources['abuseipdb'].get('abuse_confidence_score', 0)
            if abuse_score > 90:
                score += 30
                reasons.append(f"AbuseIPDB confidence: {abuse_score}% (>90%)")
            elif abuse_score > 70:
                score += 20
                reasons.append(f"AbuseIPDB confidence: {abuse_score}% (>70%)")
            elif abuse_score > 50:
                score += 10
                reasons.append(f"AbuseIPDB confidence: {abuse_score}% (>50%)")
        
        # === Threat Context/Description ===
        context = ioc_data.get('context', '').lower()
        threat_type = ioc_data.get('threat_type', '').lower()
        description = ioc_data.get('description', '').lower()
        combined_text = f"{context} {threat_type} {description}"
        
        if any(critical in combined_text for critical in self.CRITICAL_THREAT_TYPES):
            score += 25
            matching_types = [t for t in self.CRITICAL_THREAT_TYPES if t in combined_text]
            reasons.append(f"Critical threat type: {', '.join(matching_types[:2])}")
        
        # === Recency ===
        first_seen = ioc_data.get('first_seen')
        if first_seen:
            if isinstance(first_seen, str):
                try:
                    first_seen = datetime.fromisoformat(first_seen.replace('Z', '+00:00'))
                except:
                    first_seen = None
            
            if first_seen and isinstance(first_seen, datetime):
                age = datetime.utcnow() - first_seen.replace(tzinfo=None)
                if age < timedelta(days=7):
                    score += 15
                    reasons.append("Recent threat (<7 days)")
                elif age < timedelta(days=30):
                    score += 10
                    reasons.append("Recent threat (<30 days)")
        
        # === URLhaus Specific ===
        if ioc_data.get('source') == 'urlhaus':
            url_status = ioc_data.get('url_status', '').lower()
            if url_status == 'online':
                score += 20
                reasons.append("Active malware URL (online)")
            
            # Check threat type from URLhaus
            threat = ioc_data.get('threat', '').lower()
            if 'malware_download' in threat:
                score += 15
                reasons.append("Confirmed malware distribution")
        
        # === VirusTotal Reputation ===
        if 'virustotal' in sources:
            vt_reputation = sources['virustotal'].get('reputation', 0)
            if vt_reputation < -50:
                score += 20
                reasons.append(f"Negative VT reputation: {vt_reputation}")
        
        # === Multiple Sources ===
        num_sources = len(sources)
        if num_sources >= 3:
            score += 15
            reasons.append(f"Confirmed by {num_sources} sources")
        elif num_sources >= 2:
            score += 10
            reasons.append(f"Confirmed by {num_sources} sources")
        
        # === Determine Severity Level ===
        if score >= 70:
            severity = SeverityLevel.CRITICAL
        elif score >= 45:
            severity = SeverityLevel.HIGH
        elif score >= 20:
            severity = SeverityLevel.MEDIUM
        elif score > 0:
            severity = SeverityLevel.LOW
        else:
            severity = SeverityLevel.UNKNOWN
        
        # Add to IOC data
        ioc_data['severity'] = severity.value
        ioc_data['severity_score'] = score
        ioc_data['severity_reasons'] = reasons
        
        return ioc_data
    
    def calculate_batch_severity(self, iocs: list) -> list:
        """
        Calculate severity for multiple IOCs
        
        Args:
            iocs: List of enriched IOC dictionaries
            
        Returns:
            List of IOCs with severity scores
        """
        scored_iocs = []
        
        for ioc in iocs:
            scored_ioc = self.calculate_severity(ioc)
            scored_iocs.append(scored_ioc)
        
        logger.info(f"✅ Scored {len(scored_iocs)} IOCs for severity")
        
        # Log severity distribution
        severity_counts = {}
        for ioc in scored_iocs:
            severity = ioc.get('severity', 'UNKNOWN')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        logger.info(f"📊 Severity distribution: {severity_counts}")
        
        return scored_iocs
    
    def get_critical_iocs(self, iocs: list) -> list:
        """
        Filter IOCs by CRITICAL severity
        
        Args:
            iocs: List of scored IOCs
            
        Returns:
            List of CRITICAL severity IOCs
        """
        return [ioc for ioc in iocs if ioc.get('severity') == SeverityLevel.CRITICAL.value]
    
    def get_high_priority_iocs(self, iocs: list) -> list:
        """
        Filter IOCs by CRITICAL or HIGH severity
        
        Args:
            iocs: List of scored IOCs
            
        Returns:
            List of high-priority IOCs
        """
        return [
            ioc for ioc in iocs 
            if ioc.get('severity') in [SeverityLevel.CRITICAL.value, SeverityLevel.HIGH.value]
        ]


# Global instance
severity_scorer = SeverityScorer()
