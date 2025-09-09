"""
Base code analyzer agent using Gemini models
"""
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import ast
import logging
from models.gemini.gemini_client import get_gemini_client
from models.routing.model_router import get_model_router
from config.settings import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

class BaseCodeAnalyzer:
    """Base class for code analysis agents"""
    
    def __init__(self):
        """Initialize the analyzer with Gemini client"""
        self.gemini_client = get_gemini_client()
        self.model_router = get_model_router()
        self.supported_languages = SUPPORTED_LANGUAGES
    
    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        file_ext = Path(file_path).suffix.lower()
        
        for lang, config in self.supported_languages.items():
            if file_ext in config["extensions"]:
                return lang
        
        return None
    
    def read_code_file(self, file_path: str) -> str:
        """Safely read code file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check file size (from settings)
            if len(content) > 1024 * 1024:  # 1MB limit for individual files
                logger.warning(f"⚠️ File {file_path} is very large, truncating...")
                content = content[:1024*1024] + "\n\n# ... (file truncated due to size)"
            
            return content
            
        except Exception as e:
            logger.error(f"❌ Error reading file {file_path}: {e}")
            return f"# Error reading file: {str(e)}"
    
    async def analyze_single_file(self, file_path: str, analysis_type: str = "simple") -> Dict[str, Any]:
        """Analyze a single code file"""
        try:
            # Detect language
            language = self.detect_language(file_path)
            if not language:
                return {
                    "file_path": file_path,
                    "error": "Unsupported file type",
                    "supported_extensions": [ext for lang in self.supported_languages.values() for ext in lang["extensions"]]
                }
            
            # Read file content
            code_content = self.read_code_file(file_path)
            if code_content.startswith("# Error reading file"):
                return {
                    "file_path": file_path,
                    "error": "Could not read file",
                    "details": code_content
                }
            
            logger.info(f"🔍 Analyzing {file_path} ({language}) - {analysis_type} mode")
            
            # Choose analysis method
            if analysis_type == "detailed":
                result = await self.gemini_client.analyze_code_detailed(code_content, language)
            else:
                result = await self.gemini_client.analyze_code_simple(code_content, language)
            
            # Add metadata
            analysis_result = {
                "file_path": file_path,
                "language": language,
                "analysis_type": analysis_type,
                "file_size": len(code_content),
                "result": result
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Analysis failed for {file_path}: {e}")
            return {
                "file_path": file_path,
                "error": str(e),
                "analysis_type": analysis_type
            }
    
    async def analyze_directory(self, directory_path: str, analysis_type: str = "simple") -> Dict[str, Any]:
        """Analyze all supported files in a directory"""
        try:
            dir_path = Path(directory_path)
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory_path}"}
            
            # Find all supported code files
            code_files = []
            for lang_config in self.supported_languages.values():
                for ext in lang_config["extensions"]:
                    code_files.extend(dir_path.rglob(f"*{ext}"))
            
            # Remove duplicates and sort
            code_files = sorted(list(set(code_files)))
            
            logger.info(f"🔍 Found {len(code_files)} code files in {directory_path}")
            
            if not code_files:
                return {
                    "directory": directory_path,
                    "message": "No supported code files found",
                    "supported_extensions": [ext for lang in self.supported_languages.values() for ext in lang["extensions"]]
                }
            
            # Analyze files (limit to first 10 for now to avoid overwhelming)
            files_to_analyze = code_files[:10]
            if len(code_files) > 10:
                logger.info(f"⚠️ Limiting analysis to first 10 files (found {len(code_files)} total)")
            
            # Analyze files concurrently (but with limit)
            analysis_tasks = [
                self.analyze_single_file(str(file_path), analysis_type) 
                for file_path in files_to_analyze
            ]
            
            # Run with concurrency limit
            semaphore = asyncio.Semaphore(3)  # Max 3 concurrent analyses
            
            async def analyze_with_semaphore(task):
                async with semaphore:
                    return await task
            
            results = await asyncio.gather(*[
                analyze_with_semaphore(task) for task in analysis_tasks
            ])
            
            # Compile summary
            summary = {
                "directory": directory_path,
                "analysis_type": analysis_type,
                "total_files_found": len(code_files),
                "files_analyzed": len(files_to_analyze),
                "results": results,
                "languages_detected": list(set([
                    result.get("language") for result in results 
                    if result.get("language")
                ]))
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Directory analysis failed for {directory_path}: {e}")
            return {
                "directory": directory_path,
                "error": str(e),
                "analysis_type": analysis_type
            }

# Global analyzer instance
base_analyzer = None

def get_base_analyzer() -> BaseCodeAnalyzer:
    """Get or create global base analyzer instance"""
    global base_analyzer
    if base_analyzer is None:
        base_analyzer = BaseCodeAnalyzer()
    return base_analyzer
