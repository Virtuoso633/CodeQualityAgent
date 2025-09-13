"""
Specialized Performance Analysis Agent - FINAL LLM-DRIVEN VERSION
"""
import asyncio
import json
from typing import Dict, List, Any
import logging
from models.gemini.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)

class PerformanceAnalysisAgent:
    """Specialized agent for performance bottleneck analysis using exclusively LLM reasoning."""
    
    def __init__(self):
        """Initializes the agent with a connection to the Gemini client."""
        self.gemini_client = get_gemini_client()

    async def analyze_code(self, code_content: str, language: str) -> Dict[str, Any]:
        """
        Analyzes code for performance issues using Gemini, expecting a structured JSON output.
        """
        prompt = f"""
        You are an expert performance engineer. Analyze the following {language} code for performance bottlenecks.
        Identify issues related to algorithmic complexity (Big O), memory usage, and inefficient operations.

        CODE:
        ```{language}
        {code_content}
        ```

        Respond ONLY with a valid JSON object containing a single key "issues". The value must be a list of issue objects.
        Each issue object must have the following keys:
        - "line": The approximate line number of the bottleneck.
        - "severity": A string, either "High", "Medium", or "Low".
        - "type": A short description of the performance issue (e.g., "Inefficient Loop", "Excessive Memory Allocation").
        - "explanation": A clear, developer-friendly explanation of why this code is inefficient and its performance impact.
        - "fix_suggestion": A specific, actionable code snippet or detailed recommendation on how to optimize the code.

        If no issues are found, return a JSON object with an empty list: {{"issues": []}}.
        Do not include any text, markdown formatting, or code block fences like ```json around the JSON object.
        """
        try:
            # Use the Gemini client to get a response
            response_content = await self.gemini_client.analyze_code_simple(code_content, language, prompt_override=prompt)
            
            # Clean the response to ensure it's valid JSON
            json_response_str = response_content.strip().replace("```json", "").replace("```", "")
            
            # Parse the cleaned string into a Python dictionary
            return json.loads(json_response_str)

        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"❌ Failed to parse performance analysis from LLM: {e}\nRaw Response: '{response_content}'")
            return {"issues": []} # Return empty list on failure
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during performance analysis: {e}")
            return {"issues": []}

# Global instance for singleton pattern
performance_agent = None

def get_performance_agent() -> PerformanceAnalysisAgent:
    """Provides a global singleton instance of the PerformanceAnalysisAgent."""
    global performance_agent
    if performance_agent is None:
        performance_agent = PerformanceAnalysisAgent()
    return performance_agent