"""Gemini AI client for intelligent error analysis"""
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

# Try to import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Generative AI not available. Install with: pip install google-generativeai")


@dataclass
class RuleSuggestion:
    """AI-suggested healing rule"""
    pattern: str
    action_type: str
    parameters: Dict[str, Any]
    confidence: float
    reasoning: str
    example_errors: List[str]


@dataclass
class ActionSuggestion:
    """AI-suggested immediate action"""
    action_type: str
    parameters: Dict[str, Any]
    confidence: float
    reasoning: str


class GeminiClient:
    """Client for Google Gemini AI"""
    
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        if not GEMINI_AVAILABLE:
            raise RuntimeError("google-generativeai package not installed")
        
        self.api_key = api_key
        self.model_name = model
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        
        logger.info(f"Initialized Gemini client with model: {model}")
    
    async def suggest_rule_from_errors(self, errors: List[str]) -> Optional[RuleSuggestion]:
        """Analyze multiple similar errors and suggest a healing rule"""
        try:
            # Prepare prompt
            errors_text = "\n".join([f"{i+1}. {err}" for i, err in enumerate(errors[:10])])
            
            prompt = f"""You are a DevOps expert analyzing application errors to create automated healing rules.

Analyze these recurring errors and suggest ONE healing rule:

ERRORS:
{errors_text}

Provide your response in JSON format with these exact fields:
{{
    "pattern": "regex pattern to match these errors (use (?i) for case-insensitive)",
    "action_type": "one of: restart_service, cleanup_disk, kill_process",
    "parameters": {{"service_name": "app", "service_type": "docker"}},
    "confidence": 0.85,
    "reasoning": "brief explanation of why this rule helps"
}}

Rules:
- Pattern must be a valid Python regex
- Action type must be one of the three listed
- Confidence should be 0.0 to 1.0
- Keep reasoning under 100 characters
- Only suggest rules that are safe to automate"""

            # Call Gemini
            response = self.model.generate_content(prompt)
            
            # Parse response
            return self._parse_rule_suggestion(response.text, errors)
        
        except Exception as e:
            logger.error(f"Failed to get rule suggestion from Gemini: {e}")
            return None
    
    async def analyze_error(self, error_message: str, context: Optional[str] = None) -> Optional[ActionSuggestion]:
        """Analyze a single error and suggest immediate action"""
        try:
            context_text = f"\n\nContext:\n{context}" if context else ""
            
            prompt = f"""You are a DevOps expert analyzing an application error to suggest immediate remediation.

ERROR:
{error_message}{context_text}

Suggest ONE immediate action in JSON format:
{{
    "action_type": "one of: restart_service, cleanup_disk, kill_process",
    "parameters": {{"service_name": "app", "service_type": "docker"}},
    "confidence": 0.80,
    "reasoning": "brief explanation"
}}

Rules:
- Only suggest safe, automatable actions
- Confidence 0.0-1.0 (be conservative)
- Keep reasoning under 100 characters
- If unsure, set confidence below 0.7"""

            response = self.model.generate_content(prompt)
            
            return self._parse_action_suggestion(response.text)
        
        except Exception as e:
            logger.error(f"Failed to analyze error with Gemini: {e}")
            return None
    
    async def chat(self, message: str, context: Dict[str, Any]) -> str:
        """Chat interface for asking questions about incidents"""
        try:
            # Format context
            stats = context.get('stats', {})
            recent_incidents = context.get('recent_incidents', [])
            
            stats_text = f"""
Total Incidents: {stats.get('total_incidents', 0)}
Resolved: {stats.get('resolved_incidents', 0)}
Total Actions: {stats.get('total_actions', 0)}
Success Rate: {stats.get('successful_actions', 0) / max(stats.get('total_actions', 1), 1) * 100:.1f}%
"""
            
            incidents_text = "\n".join([
                f"- {inc.get('timestamp', 'N/A')}: {inc.get('message', 'N/A')[:100]}"
                for inc in recent_incidents[:5]
            ])
            
            prompt = f"""You are an AI assistant helping with a self-healing DevOps agent.

SYSTEM STATUS:
{stats_text}

RECENT INCIDENTS:
{incidents_text}

USER QUESTION:
{message}

Provide a helpful, actionable response. Be concise but informative. Focus on insights and recommendations."""

            response = self.model.generate_content(prompt)
            
            return response.text
        
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    async def analyze_root_cause(self, incident: Dict[str, Any], actions: List[Dict[str, Any]]) -> str:
        """Analyze root cause of an incident"""
        try:
            actions_text = "\n".join([
                f"- {act.get('action_type', 'N/A')}: {act.get('message', 'N/A')}"
                for act in actions
            ])
            
            prompt = f"""You are a DevOps expert performing root cause analysis.

INCIDENT:
Error: {incident.get('message', 'N/A')}
Source: {incident.get('source', 'N/A')}
Severity: {incident.get('severity', 'N/A')}
Context: {incident.get('context', 'N/A')}

ACTIONS TAKEN:
{actions_text}

Provide:
1. Root cause analysis (what caused this?)
2. Why the actions taken helped (or didn't)
3. Prevention recommendations

Keep it concise and actionable."""

            response = self.model.generate_content(prompt)
            
            return response.text
        
        except Exception as e:
            logger.error(f"Root cause analysis failed: {e}")
            return f"Analysis failed: {str(e)}"
    
    def _parse_rule_suggestion(self, response_text: str, example_errors: List[str]) -> Optional[RuleSuggestion]:
        """Parse Gemini response into RuleSuggestion"""
        try:
            # Extract JSON from response (might have markdown code blocks)
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if not json_match:
                logger.error(f"No JSON found in response: {response_text[:200]}")
                return None
            
            data = json.loads(json_match.group(0))
            
            # Validate required fields
            required = ['pattern', 'action_type', 'parameters', 'confidence', 'reasoning']
            if not all(field in data for field in required):
                logger.error(f"Missing required fields in response: {data}")
                return None
            
            # Validate action type
            valid_actions = ['restart_service', 'cleanup_disk', 'kill_process']
            if data['action_type'] not in valid_actions:
                logger.error(f"Invalid action type: {data['action_type']}")
                return None
            
            # Validate pattern is valid regex
            try:
                re.compile(data['pattern'])
            except re.error as e:
                logger.error(f"Invalid regex pattern: {data['pattern']}: {e}")
                return None
            
            return RuleSuggestion(
                pattern=data['pattern'],
                action_type=data['action_type'],
                parameters=data['parameters'],
                confidence=float(data['confidence']),
                reasoning=data['reasoning'],
                example_errors=example_errors[:5]
            )
        
        except Exception as e:
            logger.error(f"Failed to parse rule suggestion: {e}")
            return None
    
    def _parse_action_suggestion(self, response_text: str) -> Optional[ActionSuggestion]:
        """Parse Gemini response into ActionSuggestion"""
        try:
            # Extract JSON
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if not json_match:
                return None
            
            data = json.loads(json_match.group(0))
            
            # Validate
            required = ['action_type', 'parameters', 'confidence', 'reasoning']
            if not all(field in data for field in required):
                return None
            
            valid_actions = ['restart_service', 'cleanup_disk', 'kill_process']
            if data['action_type'] not in valid_actions:
                return None
            
            return ActionSuggestion(
                action_type=data['action_type'],
                parameters=data['parameters'],
                confidence=float(data['confidence']),
                reasoning=data['reasoning']
            )
        
        except Exception as e:
            logger.error(f"Failed to parse action suggestion: {e}")
            return None
