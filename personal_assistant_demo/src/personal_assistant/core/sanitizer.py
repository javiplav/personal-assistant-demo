# sanitizer.py
import re
from typing import Optional, Dict, List

# Regex patterns for PII detection
EMAIL_RE = re.compile(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b')
PHONE_RE = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b')
CC_RE = re.compile(r'\b(?:\d[ -]*?){13,19}\b')  # Simplistic, catches major lengths
IBAN_RE = re.compile(r'\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b')
SSN_RE = re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b')  # US Social Security Numbers
API_KEY_RE = re.compile(r'\b[A-Za-z0-9]{20,}\b')  # Potential API keys (20+ chars alphanumeric)

class PIISanitizer:
    """Fast regex-based PII detection and sanitization"""
    
    def __init__(self, max_length: int = 10000):
        """
        Initialize sanitizer with configurable limits
        
        Args:
            max_length: Maximum allowed text length before truncation
        """
        self.max_length = max_length
        self.patterns = {
            'EMAIL': EMAIL_RE,
            'PHONE': PHONE_RE, 
            'CARD': CC_RE,
            'IBAN': IBAN_RE,
            'SSN': SSN_RE,
            'API_KEY': API_KEY_RE
        }
    
    def sanitize(self, text: str, preserve_structure: bool = True) -> str:
        """
        Sanitize text by replacing PII with redacted tokens
        
        Args:
            text: Input text to sanitize
            preserve_structure: If True, maintain original text structure
            
        Returns:
            Sanitized text with PII replaced by [REDACTED:TYPE] tokens
        """
        if not text:
            return text
            
        # Truncate if too long
        if len(text) > self.max_length:
            text = text[:self.max_length] + "...[TRUNCATED]"
        
        # Apply PII redaction patterns
        sanitized = text
        for pii_type, pattern in self.patterns.items():
            replacement = f'[REDACTED:{pii_type}]'
            sanitized = pattern.sub(replacement, sanitized)
        
        # Remove control characters but preserve basic formatting
        if preserve_structure:
            sanitized = ''.join(ch for ch in sanitized if ch.isprintable() or ch in '\n\r\t ')
        else:
            sanitized = ''.join(ch for ch in sanitized if ch.isprintable())
            
        return sanitized
    
    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """
        Detect PII without sanitizing, returning found instances
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary mapping PII types to lists of found instances
        """
        if not text:
            return {}
            
        detected = {}
        for pii_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected[pii_type] = matches
                
        return detected
    
    def sanitize_with_metadata(self, text: str) -> Dict[str, any]:
        """
        Sanitize text and return metadata about what was redacted
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Dictionary with 'sanitized_text', 'detected_pii', and 'redaction_count'
        """
        if not text:
            return {
                'sanitized_text': text,
                'detected_pii': {},
                'redaction_count': 0
            }
            
        detected = self.detect_pii(text)
        sanitized = self.sanitize(text)
        redaction_count = sum(len(instances) for instances in detected.values())
        
        return {
            'sanitized_text': sanitized,
            'detected_pii': detected,
            'redaction_count': redaction_count
        }


# Global sanitizer instance with default configuration
_default_sanitizer = PIISanitizer()

def sanitize(text: str) -> str:
    """
    Quick sanitization function using default settings
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text with PII redacted
    """
    return _default_sanitizer.sanitize(text)

def detect_pii(text: str) -> Dict[str, List[str]]:
    """
    Quick PII detection function using default settings
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dictionary mapping PII types to found instances
    """
    return _default_sanitizer.detect_pii(text)

def sanitize_observation(observation: str, preserve_structure: bool = True) -> str:
    """
    Sanitize tool observation before sending to LLM or logs
    
    Args:
        observation: Tool execution result or observation
        preserve_structure: Whether to preserve text formatting
        
    Returns:
        Sanitized observation safe for LLM consumption
    """
    if not observation:
        return observation
        
    # Apply PII sanitization
    sanitized = _default_sanitizer.sanitize(observation, preserve_structure)
    
    # Additional safety: Ensure we don't exceed typical LLM context limits
    max_obs_length = 2000  # Conservative limit for observations
    if len(sanitized) > max_obs_length:
        sanitized = sanitized[:max_obs_length] + "...[OBSERVATION_TRUNCATED]"
    
    return sanitized
