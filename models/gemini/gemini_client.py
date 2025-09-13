"""
Gemini model client for CodeQualityAgent - FINAL VERSION
"""
import asyncio
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import google.generativeai as genai
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiClient:
    """Main Gemini client for code analysis, supporting specialized prompts."""
    
    def __init__(self):
        try:
            if not settings.gemini_api_key:
                raise ValueError("GEMINI_API_KEY environment variable is required")
            
            genai.configure(api_key=settings.gemini_api_key)
            
            self.primary_model = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash", # Updated model name
                google_api_key=settings.gemini_api_key,
                temperature=0.1,
                max_tokens=4000
            )
            
            self.complex_model = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro", # Updated model name
                google_api_key=settings.gemini_api_key,
                temperature=0.1,
                max_tokens=8000
            )
            logger.info("✅ Gemini models initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini models: {e}")
            raise
    
    async def analyze_code_simple(self, code: str, language: str, prompt_override: Optional[str] = None) -> str:
        """
        Simple code analysis, now with prompt override for specialized agents.
        """
        try:
            # If a custom prompt is provided by an agent, use it directly.
            prompt = prompt_override if prompt_override else f"""
            Analyze this {language} code and provide a brief quality assessment.
            Code: ```{code}```
            Provide: 1. Overall quality (1-10). 2. Main issues. 3. Quick suggestions.
            """
            
            response = await self.primary_model.ainvoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            logger.error(f"❌ Simple analysis failed: {e}")
            return f"Analysis failed: {str(e)}"
    
    async def test_connection(self) -> bool:
        try:
            response = await self.primary_model.ainvoke([HumanMessage(content="Say 'Hello'")])
            return "hello" in response.content.lower()
        except Exception as e:
            logger.error(f"❌ Gemini connection test failed: {e}")
            return False

# Global client instance
gemini_client = None
def get_gemini_client() -> GeminiClient:
    global gemini_client
    if gemini_client is None:
        gemini_client = GeminiClient()
    return gemini_client