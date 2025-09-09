"""
Model routing and fallback system using LiteLLM
"""
import asyncio
from typing import Dict, List, Optional, Any
import litellm
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class ModelRouter:
    """Routes requests to appropriate models with fallback support"""
    
    def __init__(self):
        """Initialize model router with LiteLLM"""
        try:
            # Configure LiteLLM
            litellm.api_key = settings.gemini_api_key
            litellm.set_verbose = True if settings.debug else False
            
            # Model configurations
            self.models = {
                "primary": settings.primary_model,      # gemini/gemini-2.5-flash
                "complex": settings.complex_model,      # gemini/gemini-2.5-pro  
                "fallback": settings.fallback_model     # openai/gpt-4o-mini (if needed)
            }
            
            logger.info("✅ Model router initialized with LiteLLM")
            
        except Exception as e:
            logger.error(f"❌ Model router initialization failed: {e}")
            raise
    
    async def route_request(self, 
                          prompt: str, 
                          complexity: str = "normal",
                          max_retries: int = 2) -> Dict[str, Any]:
        """Route request to appropriate model with fallback"""
        
        # Choose model based on complexity
        if complexity == "high" or complexity == "detailed":
            primary_model = self.models["complex"]
        else:
            primary_model = self.models["primary"]
        
        # Try primary model first
        for attempt in range(max_retries):
            try:
                logger.info(f"🚀 Attempting request with {primary_model} (attempt {attempt + 1})")
                
                response = await litellm.acompletion(
                    model=primary_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=4000 if complexity == "normal" else 8000
                )
                
                return {
                    "success": True,
                    "content": response.choices[0].message.content,
                    "model_used": primary_model,
                    "attempt": attempt + 1,
                    "usage": response.usage.dict() if response.usage else None
                }
                
            except Exception as e:
                logger.warning(f"⚠️ Attempt {attempt + 1} failed with {primary_model}: {e}")
                
                if attempt == max_retries - 1:
                    # Last attempt, try fallback if available
                    if settings.fallback_model and settings.fallback_model != primary_model:
                        try:
                            logger.info(f"🔄 Trying fallback model: {settings.fallback_model}")
                            
                            response = await litellm.acompletion(
                                model=settings.fallback_model,
                                messages=[{"role": "user", "content": prompt}],
                                temperature=0.1,
                                max_tokens=4000
                            )
                            
                            return {
                                "success": True,
                                "content": response.choices[0].message.content,
                                "model_used": settings.fallback_model,
                                "attempt": "fallback",
                                "usage": response.usage.dict() if response.usage else None
                            }
                            
                        except Exception as fallback_error:
                            logger.error(f"❌ Fallback model also failed: {fallback_error}")
                
                # Wait before retry
                await asyncio.sleep(1)
        
        # All attempts failed
        return {
            "success": False,
            "error": f"All model attempts failed after {max_retries} retries",
            "model_used": None,
            "content": None
        }
    
    async def test_all_models(self) -> Dict[str, bool]:
        """Test connectivity to all configured models"""
        results = {}
        test_prompt = "Respond with 'OK' if you receive this test message."
        
        for model_name, model_id in self.models.items():
            if not model_id or model_id == "openai/gpt-4o-mini":  # Skip if no API key
                results[model_name] = False
                continue
                
            try:
                response = await litellm.acompletion(
                    model=model_id,
                    messages=[{"role": "user", "content": test_prompt}],
                    max_tokens=10
                )
                
                results[model_name] = "ok" in response.choices[0].message.content.lower()
                logger.info(f"✅ {model_name} ({model_id}): Connected")
                
            except Exception as e:
                results[model_name] = False
                logger.error(f"❌ {model_name} ({model_id}): {e}")
        
        return results

# Global router instance
model_router = None

def get_model_router() -> ModelRouter:
    """Get or create global model router instance"""
    global model_router
    if model_router is None:
        model_router = ModelRouter()
    return model_router
