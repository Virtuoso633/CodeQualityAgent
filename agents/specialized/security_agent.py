"""
Specialized Security Analysis Agent - FINAL LLM-DRIVEN VERSION
"""
import asyncio
import json
from typing import Dict, List, Any
import logging
from models.gemini.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)

class SecurityAnalysisAgent:
    """Specialized agent for security vulnerability analysis using exclusively LLM reasoning."""
    
    def __init__(self):
        """Initializes the agent with a connection to the Gemini client."""
        self.gemini_client = get_gemini_client()

    async def analyze_code(self, code_content: str, language: str) -> Dict[str, Any]:
        """
        Analyzes code for security vulnerabilities using Gemini, expecting a structured JSON output.
        """
        prompt = f"""
        You are an expert cybersecurity analyst. Analyze the following {language} code for security vulnerabilities.
        Identify issues based on OWASP Top 10 and common weaknesses (CWE).

        CODE:
        ```{language}
        {code_content}
        ```

        Respond ONLY with a valid JSON object containing a single key "issues". The value must be a list of issue objects.
        Each issue object must have the following keys:
        - "line": The approximate line number of the vulnerability.
        - "severity": A string, either "Critical", "High", "Medium", or "Low".
        - "type": A short description of the vulnerability type (e.g., "SQL Injection", "Hardcoded Secret").
        - "explanation": A clear, developer-friendly explanation of why this is a vulnerability and what its impact is.
        - "fix_suggestion": A specific, actionable code snippet or detailed recommendation on how to fix the issue.

        If no issues are found, return a JSON object with an empty list: {{"issues": []}}.
        Do not include any text, markdown formatting, or code block fences like ```json around the JSON object.
        """
        try:
            # Use the Gemini client to get a response
            response_content = await self.gemini_client.analyze_code_simple(code_content, language, prompt_override=prompt)
            
            # Clean the response to ensure it's valid JSON
            # LLMs can sometimes add extra text or formatting
            json_response_str = response_content.strip().replace("```json", "").replace("```", "")
            
            # Parse the cleaned string into a Python dictionary
            return json.loads(json_response_str)
            
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"❌ Failed to parse security analysis from LLM: {e}\nRaw Response: '{response_content}'")
            return {"issues": []} # Return empty list on failure to avoid crashes
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during security analysis: {e}")
            return {"issues": []}

# Global instance for singleton pattern
security_agent = None

def get_security_agent() -> SecurityAnalysisAgent:
    """Provides a global singleton instance of the SecurityAnalysisAgent."""
    global security_agent
    if security_agent is None:
        security_agent = SecurityAnalysisAgent()
    return security_agent