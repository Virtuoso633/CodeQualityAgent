"""
Gemini model client for CodeQualityAgent - FIXED
"""
import os
import asyncio
from typing import Dict, List, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
import google.generativeai as genai
from config.settings import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiClient:
    """Main Gemini client for code analysis - FIXED VERSION"""
    
    def __init__(self):
        """Initialize Gemini client with API key authentication"""
        try:
            # Configure the genai library directly with API key
            if not settings.gemini_api_key:
                raise ValueError("GEMINI_API_KEY environment variable is required")
            
            genai.configure(api_key=settings.gemini_api_key)
            
            # Initialize ChatGoogleGenerativeAI with explicit API key
            self.primary_model = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",  # Use gemini-flash instead of 2.5-flash
                google_api_key=settings.gemini_api_key,  # Explicit API key
                temperature=0.1,
                max_tokens=4000
            )
            
            self.complex_model = ChatGoogleGenerativeAI(
                model="gemini-2.5-pro",  # Use same model for consistency
                google_api_key=settings.gemini_api_key,  # Explicit API key
                temperature=0.1,
                max_tokens=8000
            )
            
            logger.info("✅ Gemini models initialized with API key successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini models: {e}")
            raise
    
    async def analyze_code_simple(self, code: str, language: str) -> str:
        """Simple code analysis using primary model"""
        try:
            prompt = f"""
            Analyze this {language} code and provide a brief quality assessment:
            
            Code:
            ```
            {code}
            ```
            
            Please provide:
            1. Overall code quality (1-10 scale)
            2. Main issues found (if any)
            3. Quick improvement suggestions
            
            Keep response concise and developer-friendly.
            """
            
            response = await self.primary_model.ainvoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            logger.error(f"❌ Simple analysis failed: {e}")
            return f"Analysis failed: {str(e)}"
    
    async def analyze_code_detailed(self, code: str, language: str) -> Dict[str, Any]:
        """Detailed code analysis using complex model"""
        try:
            prompt = f"""
            Perform detailed code quality analysis for this {language} code:
            
            Code:
            ```
            {code}
            ```
            
            Analyze and provide structured output for:
            
            1. SECURITY ISSUES:
            - Potential vulnerabilities
            - Security risks
            - Suggested fixes
            
            2. PERFORMANCE ISSUES:
            - Bottlenecks or inefficiencies  
            - Memory usage concerns
            - Optimization suggestions
            
            3. CODE QUALITY:
            - Readability issues
            - Maintainability concerns
            - Best practice violations
            
            4. OVERALL ASSESSMENT:
            - Quality score (1-10)
            - Priority issues to fix
            - Improvement recommendations
            
            Format as clear, actionable feedback for developers.
            """
            
            response = await self.complex_model.ainvoke([HumanMessage(content=prompt)])
            
            # Structure the response
            analysis_result = {
                "language": language,
                "analysis_type": "detailed",
                "content": response.content,
                "model_used": "gemini-pro",
                "timestamp": str(asyncio.get_event_loop().time())
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Detailed analysis failed: {e}")
            return {
                "error": str(e),
                "analysis_type": "failed",
                "content": f"Detailed analysis failed: {str(e)}"
            }
    
    async def test_connection(self) -> bool:
        """Test Gemini API connection"""
        try:
            test_prompt = "Say 'Hello' if you can receive this message."
            response = await self.primary_model.ainvoke([HumanMessage(content=test_prompt)])
            
            if "hello" in response.content.lower():
                logger.info("✅ Gemini connection test successful")
                return True
            else:
                logger.warning("⚠️ Gemini responded but unexpectedly")
                return False
                
        except Exception as e:
            logger.error(f"❌ Gemini connection test failed: {e}")
            return False

# Global client instance
gemini_client = None

def get_gemini_client() -> GeminiClient:
    """Get or create global Gemini client instance"""
    global gemini_client
    if gemini_client is None:
        gemini_client = GeminiClient()
    return gemini_client
