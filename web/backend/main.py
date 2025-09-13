"""
FastAPI Backend for Code Quality Intelligence Agent - FINAL BUGFIXED VERSION
"""
import asyncio
import shutil
import tempfile
import sys
import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from datetime import datetime
import uuid
from dataclasses import asdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from config.settings import settings
from tools.analyzers.comprehensive_scanner import ComprehensiveCodebaseScanner, CodebaseAnalysis
from tools.analyzers.rag_analyzer import RAGCodeAnalyzer
from flows.interactive.qa_system import get_qa_system
from flows.analysis.crew_coordinator import get_crew_coordinator

# --- INITIALIZATION ---
comprehensive_scanner = ComprehensiveCodebaseScanner()
rag_analyzer = RAGCodeAnalyzer()
qa_system = get_qa_system()
crew_coordinator = get_crew_coordinator()
RAG_INDEX_DIR = Path("data/rag_indexes")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="🤖 Code Quality Intelligence API - RAG Integrated", version="2.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class InteractiveQueryRequest(BaseModel):
    query: str = Field(...)
    session_id: str = Field(...)
    analysis_id: str = Field(...)

analysis_cache: Dict[str, Dict[str, Any]] = {}

@app.get("/")
async def root():
    return {"message": "Code Quality Intelligence API - RAG Integrated and Operational"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.post("/analyze/comprehensive")
async def analyze_comprehensive_codebase(
    background_tasks: BackgroundTasks,
    github_url: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
):
    analysis_id = str(uuid.uuid4())
    temp_dir = None
    try:
        if github_url and github_url.startswith("https://github.com/"):
            source_path = github_url
            source_type = "github"
        elif files:
            temp_dir = tempfile.mkdtemp()
            for file in files:
                (Path(temp_dir) / file.filename).write_bytes(await file.read())
            source_path = temp_dir
            source_type = "upload"
        else:
            raise HTTPException(400, "Either a valid github_url or files must be provided.")

        analysis_cache[analysis_id] = {"status": "processing", "analysis_id": analysis_id}
        background_tasks.add_task(run_analysis_and_build_rag, analysis_id, source_path, source_type)
        return {"status": "processing", "analysis_id": analysis_id}
    except Exception as e:
        if temp_dir: shutil.rmtree(temp_dir, ignore_errors=True)
        logger.error(f"❌ Analysis initiation failed: {e}")
        raise HTTPException(500, f"Failed to start analysis: {str(e)}")

async def run_analysis_and_build_rag(analysis_id: str, path: str, source_type: str):
    cloned_path = path
    try:
        if source_type == "github":
            cloned_path = await comprehensive_scanner._clone_github_repo(path)
        
        analysis_cache[analysis_id]["status"] = "analyzing"
        
        # --- FIX: REMOVED THE EXTRA `{}` ARGUMENT ---
        report_task = comprehensive_scanner.scan_codebase(cloned_path)
        rag_task = rag_analyzer.build_codebase_index(cloned_path)
        
        results, rag_success = await asyncio.gather(report_task, rag_task)
        
        serializable_results = asdict(results)

        logger.info(f"🧠 CrewAI starting summary for {analysis_id}...")
        all_issues = {
            "security": [issue for file in results.file_analyses.values() for issue in file.security_issues],
            "performance": [issue for file in results.file_analyses.values() for issue in file.performance_issues],
        }
        summary = await crew_coordinator.generate_executive_summary(json.dumps(all_issues, indent=2))
        serializable_results["crew_ai_summary"] = summary
        
        if rag_success:
            index_path = RAG_INDEX_DIR / f"{analysis_id}.faiss"
            rag_analyzer.save_index(index_path)
            serializable_results["rag_index_path"] = str(index_path)

        analysis_cache[analysis_id].update({
            "status": "completed",
            "results": serializable_results,
            "completed_at": datetime.now().isoformat(),
        })
        logger.info(f"✅ Analysis & RAG build for {analysis_id} completed.")
    except Exception as e:
        logger.error(f"❌ Background task for {analysis_id} failed: {e}")
        analysis_cache[analysis_id].update({"status": "failed", "error": str(e)})
    finally:
        if source_type in ["github", "upload"] and os.path.isdir(cloned_path):
            shutil.rmtree(cloned_path, ignore_errors=True)

@app.get("/analyze/{analysis_id}/status")
async def get_analysis_status(analysis_id: str):
    if analysis_id not in analysis_cache:
        raise HTTPException(404, "Analysis not found")
    return analysis_cache[analysis_id]

@app.post("/chat/summary_query")
async def summary_query_with_context(request: InteractiveQueryRequest):
    try:
        analysis = analysis_cache.get(request.analysis_id)
        if not analysis or analysis.get("status") != "completed":
            raise HTTPException(404, "Analysis context not ready or found.")
        
        results = analysis["results"]
        context_summary = f"""Analysis Summary: Total Files: {results.get('total_files')}, Languages: {list(results.get('languages_detected', {}).keys())}, Overall Score: {results.get('overall_scores', {}).get('overall')}/10."""
        
        response = await qa_system.ask_question(request.query, context_override=context_summary)
        return {"status": "success", "response": response}
    except Exception as e:
        raise HTTPException(500, f"Failed to process summary query: {str(e)}")

@app.post("/chat/rag_query")
async def rag_query_with_context(request: InteractiveQueryRequest):
    try:
        analysis = analysis_cache.get(request.analysis_id)
        if not analysis or analysis.get("status") != "completed":
            raise HTTPException(404, "Analysis context not ready or found.")
        
        index_path_str = analysis["results"].get("rag_index_path")
        if not index_path_str:
            raise HTTPException(404, "RAG index not available for this analysis.")
            
        local_rag_analyzer = RAGCodeAnalyzer()
        local_rag_analyzer.load_index(Path(index_path_str))
        
        response = await local_rag_analyzer.query_codebase(request.query)
        return {"status": "success", "response": response}
    except Exception as e:
        logger.error(f"❌ RAG query failed: {e}")
        raise HTTPException(500, f"Failed to process RAG query: {str(e)}")

if __name__ == "__main__":
    RAG_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    uvicorn.run("web.backend.main:app", host=settings.web_host, port=settings.web_port, reload=True)