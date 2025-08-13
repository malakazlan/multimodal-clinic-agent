"""
Healthcare Safety Filter for the Healthcare Voice AI Assistant.
Blocks unsafe content and ensures healthcare compliance.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from loguru import logger

from config.settings import get_settings


class RiskLevel(Enum):
    """Risk levels for content safety."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented
    
    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented
    
    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented
    
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented


@dataclass
class SafetyResult:
    """Result from content safety check."""
    is_safe: bool
    risk_level: RiskLevel
    reason: str
    flagged_content: List[str] = None
    suggestions: List[str] = None


class HealthcareSafetyFilter:
    """Filter for healthcare content safety and compliance."""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Define unsafe patterns
        self.unsafe_patterns = self._initialize_unsafe_patterns()
        
        # Define medical advice patterns
        self.medical_advice_patterns = self._initialize_medical_advice_patterns()
        
        # Define disclaimers
        self.disclaimers = self._initialize_disclaimers()
        
        logger.info("Healthcare safety filter initialized")
    
    def _initialize_unsafe_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for unsafe content detection."""
        return {
            "critical": [
                r"\b(diagnose|diagnosis|diagnosed)\b",
                r"\b(treat|treatment|treating)\b",
                r"\b(prescribe|prescription|medication)\b",
                r"\b(surgery|surgical|operation)\b",
                r"\b(prognosis|outcome|survival)\b",
                r"\b(emergency|urgent|immediate)\b",
                r"\b(deadly|fatal|lethal)\b",
                r"\b(cancer|cancerous|malignant)\b",
                r"\b(heart attack|stroke|seizure)\b"
            ],
            "high": [
                r"\b(symptom|symptoms)\b",
                r"\b(pain|hurting|ache)\b",
                r"\b(fever|temperature|hot)\b",
                r"\b(bleeding|blood|wound)\b",
                r"\b(nausea|vomiting|dizzy)\b",
                r"\b(breathing|breathless|choking)\b",
                r"\b(chest pain|heart|cardiac)\b",
                r"\b(headache|migraine|pressure)\b"
            ],
            "medium": [
                r"\b(medicine|pill|drug)\b",
                r"\b(dose|dosage|amount)\b",
                r"\b(side effect|reaction|allergy)\b",
                r"\b(test|testing|exam)\b",
                r"\b(result|finding|abnormal)\b",
                r"\b(risk|dangerous|harmful)\b"
            ],
            "low": [
                r"\b(healthy|wellness|fitness)\b",
                r"\b(nutrition|diet|vitamin)\b",
                r"\b(exercise|workout|activity)\b",
                r"\b(sleep|rest|relaxation)\b",
                r"\b(prevention|prevent|avoid)\b"
            ]
        }
    
    def _initialize_medical_advice_patterns(self) -> List[str]:
        """Initialize patterns for medical advice detection."""
        return [
            r"\b(you should|you need to|you must)\b",
            r"\b(I recommend|I suggest|I advise)\b",
            r"\b(take this|use this|try this)\b",
            r"\b(apply|administer|inject)\b",
            r"\b(continue|stop|start)\b",
            r"\b(change|modify|adjust)\b",
            r"\b(combine|mix|add)\b",
            r"\b(avoid|prevent|stop)\b"
        ]
    
    def _initialize_disclaimers(self) -> Dict[str, str]:
        """Initialize healthcare disclaimers."""
        return {
            "general": "This information is for educational purposes only and should not be considered medical advice.",
            "symptoms": "If you're experiencing these symptoms, please consult with a healthcare professional immediately.",
            "medication": "Always consult with your doctor or pharmacist before taking any medication.",
            "treatment": "Treatment decisions should be made by qualified healthcare professionals based on your specific situation.",
            "emergency": "If you're experiencing a medical emergency, call emergency services immediately."
        }
    
    async def check_content(
        self,
        content: str,
        content_type: str = "general"
    ) -> SafetyResult:
        """
        Check content for safety and compliance.
        
        Args:
            content: Content to check
            content_type: Type of content (user_input, ai_response, etc.)
            
        Returns:
            SafetyResult with safety assessment
        """
        try:
            if not content or not content.strip():
                return SafetyResult(
                    is_safe=True,
                    risk_level=RiskLevel.LOW,
                    reason="Empty content"
                )
            
            # Check for unsafe patterns
            risk_assessment = self._assess_content_risk(content)
            
            # Check for medical advice patterns
            medical_advice_detected = self._detect_medical_advice(content)
            
            # Determine overall safety
            is_safe = self._determine_safety(risk_assessment, medical_advice_detected)
            risk_level = self._determine_risk_level(risk_assessment, medical_advice_detected)
            
            # Generate reason and suggestions
            reason = self._generate_safety_reason(risk_assessment, medical_advice_detected)
            suggestions = self._generate_safety_suggestions(risk_assessment, medical_advice_detected)
            
            # Log safety check
            self._log_safety_check(content, is_safe, risk_level, reason)
            
            return SafetyResult(
                is_safe=is_safe,
                risk_level=risk_level,
                reason=reason,
                flagged_content=risk_assessment.get("flagged_content", []),
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"Content safety check failed: {str(e)}", exc_info=True)
            # Default to unsafe in case of error
            return SafetyResult(
                is_safe=False,
                risk_level=RiskLevel.HIGH,
                reason=f"Safety check failed: {str(e)}"
            )
    
    def _assess_content_risk(self, content: str) -> Dict[str, Any]:
        """Assess content risk based on unsafe patterns."""
        risk_assessment = {
            "risk_scores": {},
            "flagged_content": [],
            "total_risk": 0
        }
        
        content_lower = content.lower()
        
        for risk_level, patterns in self.unsafe_patterns.items():
            risk_score = 0
            flagged_items = []
            
            for pattern in patterns:
                matches = re.findall(pattern, content_lower, re.IGNORECASE)
                if matches:
                    risk_score += len(matches)
                    flagged_items.extend(matches)
            
            risk_assessment["risk_scores"][risk_level] = risk_score
            
            if risk_score > 0:
                risk_assessment["flagged_content"].extend(flagged_items)
                
                # Weight risk levels
                if risk_level == "critical":
                    risk_assessment["total_risk"] += risk_score * 10
                elif risk_level == "high":
                    risk_assessment["total_risk"] += risk_score * 5
                elif risk_level == "medium":
                    risk_assessment["total_risk"] += risk_score * 2
                else:  # low
                    risk_assessment["total_risk"] += risk_score * 1
        
        return risk_assessment
    
    def _detect_medical_advice(self, content: str) -> Dict[str, Any]:
        """Detect medical advice patterns in content."""
        advice_detection = {
            "patterns_found": [],
            "advice_count": 0,
            "severity": "none"
        }
        
        content_lower = content.lower()
        
        for pattern in self.medical_advice_patterns:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            if matches:
                advice_detection["patterns_found"].extend(matches)
                advice_detection["advice_count"] += len(matches)
        
        # Determine severity
        if advice_detection["advice_count"] >= 3:
            advice_detection["severity"] = "high"
        elif advice_detection["advice_count"] >= 1:
            advice_detection["severity"] = "medium"
        
        return advice_detection
    
    def _determine_safety(
        self,
        risk_assessment: Dict[str, Any],
        medical_advice: Dict[str, Any]
    ) -> bool:
        """Determine if content is safe based on risk assessment."""
        # Check critical risk threshold
        if risk_assessment["total_risk"] >= 20:
            return False
        
        # Check medical advice severity
        if medical_advice["severity"] == "high":
            return False
        
        # Check for critical patterns
        if risk_assessment["risk_scores"].get("critical", 0) > 0:
            return False
        
        return True
    
    def _determine_risk_level(
        self,
        risk_assessment: Dict[str, Any],
        medical_advice: Dict[str, Any]
    ) -> RiskLevel:
        """Determine overall risk level."""
        total_risk = risk_assessment["total_risk"]
        advice_severity = medical_advice["severity"]
        
        if total_risk >= 30 or advice_severity == "high":
            return RiskLevel.CRITICAL
        elif total_risk >= 20 or advice_severity == "medium":
            return RiskLevel.HIGH
        elif total_risk >= 10:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_safety_reason(
        self,
        risk_assessment: Dict[str, Any],
        medical_advice: Dict[str, Any]
    ) -> str:
        """Generate reason for safety assessment."""
        reasons = []
        
        # Add risk-based reasons
        if risk_assessment["total_risk"] > 0:
            reasons.append(f"Content contains {risk_assessment['total_risk']} risk indicators")
        
        # Add medical advice reasons
        if medical_advice["advice_count"] > 0:
            reasons.append(f"Contains {medical_advice['advice_count']} medical advice patterns")
        
        if not reasons:
            return "Content appears safe and compliant"
        
        return "; ".join(reasons)
    
    def _generate_safety_suggestions(
        self,
        risk_assessment: Dict[str, Any],
        medical_advice: Dict[str, Any]
    ) -> List[str]:
        """Generate suggestions for improving content safety."""
        suggestions = []
        
        # General suggestions
        suggestions.append("Always consult healthcare professionals for medical concerns")
        suggestions.append("Focus on educational information rather than advice")
        suggestions.append("Include appropriate disclaimers")
        
        # Specific suggestions based on findings
        if medical_advice["advice_count"] > 0:
            suggestions.append("Avoid direct medical recommendations")
            suggestions.append("Use conditional language (e.g., 'may help' instead of 'will help')")
        
        if risk_assessment["risk_scores"].get("critical", 0) > 0:
            suggestions.append("Remove or rephrase critical medical terms")
            suggestions.append("Add emergency disclaimers where appropriate")
        
        return suggestions
    
    def _log_safety_check(
        self,
        content: str,
        is_safe: bool,
        risk_level: RiskLevel,
        reason: str
    ):
        """Log safety check results."""
        content_preview = content[:100] + "..." if len(content) > 100 else content
        
        if is_safe:
            logger.debug(f"Content safety check passed: {risk_level.name} risk")
        else:
            logger.warning(f"Content safety check failed: {risk_level.name} risk - {reason}")
        
        # Log detailed information for high-risk content
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            logger.warning(f"High-risk content detected: {content_preview}")
    
    async def generate_safe_response(self, user_message: str) -> str:
        """
        Generate a safe fallback response when unsafe content is detected.
        
        Args:
            user_message: User's original message
            
        Returns:
            Safe response text
        """
        try:
            # Analyze user message to determine appropriate response type
            if self._contains_emergency_keywords(user_message):
                return self._generate_emergency_response()
            elif self._contains_symptom_keywords(user_message):
                return self._generate_symptom_response()
            elif self._contains_treatment_keywords(user_message):
                return self._generate_treatment_response()
            else:
                return self._generate_general_safe_response()
                
        except Exception as e:
            logger.error(f"Failed to generate safe response: {str(e)}", exc_info=True)
            return self.disclaimers["general"]
    
    def _contains_emergency_keywords(self, message: str) -> bool:
        """Check if message contains emergency keywords."""
        emergency_keywords = [
            "emergency", "urgent", "immediate", "severe", "critical",
            "pain", "bleeding", "unconscious", "breathing", "heart"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in emergency_keywords)
    
    def _contains_symptom_keywords(self, message: str) -> bool:
        """Check if message contains symptom keywords."""
        symptom_keywords = [
            "symptom", "feeling", "experiencing", "noticing", "having"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in symptom_keywords)
    
    def _contains_treatment_keywords(self, message: str) -> bool:
        """Check if message contains treatment keywords."""
        treatment_keywords = [
            "treat", "cure", "fix", "help", "solution", "remedy"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in treatment_keywords)
    
    def _generate_emergency_response(self) -> str:
        """Generate response for emergency-related queries."""
        return (
            "I understand you may be experiencing concerning symptoms. "
            "If you're experiencing a medical emergency, please call emergency services immediately. "
            "For non-emergency concerns, I recommend consulting with a healthcare professional "
            "who can properly assess your situation and provide appropriate guidance."
        )
    
    def _generate_symptom_response(self) -> str:
        """Generate response for symptom-related queries."""
        return (
            "I can provide general information about symptoms, but I cannot diagnose or assess "
            "your specific situation. If you're concerned about symptoms you're experiencing, "
            "please consult with a healthcare professional who can properly evaluate your condition "
            "and provide appropriate medical advice."
        )
    
    def _generate_treatment_response(self) -> str:
        """Generate response for treatment-related queries."""
        return (
            "I can provide educational information about treatments, but I cannot recommend "
            "specific treatments for your situation. Treatment decisions should be made by "
            "qualified healthcare professionals based on your individual medical history, "
            "current condition, and other relevant factors."
        )
    
    def _generate_general_safe_response(self) -> str:
        """Generate general safe response."""
        return (
            "I'm here to provide helpful healthcare information and answer your questions. "
            "However, for any medical concerns, diagnosis, or treatment recommendations, "
            "please consult with qualified healthcare professionals who can provide "
            "personalized medical advice based on your specific situation."
        )
    
    def get_disclaimer(self, disclaimer_type: str = "general") -> str:
        """
        Get appropriate disclaimer for content type.
        
        Args:
            disclaimer_type: Type of disclaimer needed
            
        Returns:
            Appropriate disclaimer text
        """
        return self.disclaimers.get(disclaimer_type, self.disclaimers["general"])
    
    async def health_check(self) -> bool:
        """
        Perform health check on the safety filter.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Test with safe content
            safe_result = await self.check_content("Hello, how are you?")
            if not safe_result.is_safe:
                return False
            
            # Test with unsafe content
            unsafe_result = await self.check_content("You should take this medicine for your symptoms")
            if unsafe_result.is_safe:
                return False
            
            logger.debug("Healthcare safety filter health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Healthcare safety filter health check failed: {str(e)}", exc_info=True)
            return False
