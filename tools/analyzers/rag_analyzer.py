"""
RAG-based analyzer for large codebase understanding - FINAL UI-FRIENDLY VERSION
"""
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from config.settings import settings

logger = logging.getLogger(__name__)

class RAGCodeAnalyzer:
    """RAG-based analyzer for understanding large codebases"""

    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=settings.gemini_api_key)
        self.gemini_model = ChatGoogleGenerativeAI(model="gemini-2.5-pro", google_api_key=settings.gemini_api_key, temperature=0.1)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200, separators=["\n\n", "\n", " ", ""])
        self.vector_store: Optional[FAISS] = None

    def _collect_code_files(self, directory_path: str) -> List[Path]:
        from config.settings import SUPPORTED_LANGUAGES
        dir_path = Path(directory_path)
        if not dir_path.is_dir(): return []
        extensions = [ext for lang in SUPPORTED_LANGUAGES.values() for ext in lang["extensions"]]
        return sorted([f for ext in extensions for f in dir_path.rglob(f"*{ext}")])

    def _detect_language(self, file_path: Path) -> str:
        from config.settings import SUPPORTED_LANGUAGES
        ext = file_path.suffix.lower()
        for lang, config in SUPPORTED_LANGUAGES.items():
            if ext in config["extensions"]: return lang
        return "unknown"

    async def build_codebase_index(self, codebase_path: str, max_files: int = 200) -> bool:
        """Builds RAG index and prepares it for saving."""
        try:
            code_root = Path(codebase_path)
            logger.info(f"🔍 RAG: Building index for {code_root}")
            code_files = self._collect_code_files(codebase_path)

            if not code_files: return False

            documents, metadatas = [], []
            for file_path in code_files[:max_files]:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    chunks = self.text_splitter.split_text(content)
                    
                    # --- FIX: STORE A CLEAN, RELATIVE PATH ---
                    relative_path = file_path.relative_to(code_root)
                    
                    for chunk in chunks:
                        documents.append(chunk)
                        metadatas.append({"source": str(relative_path), "language": self._detect_language(file_path)})
                except Exception as e:
                    logger.warning(f"⚠️ RAG: Skipping file {file_path}: {e}")
                    continue

            if not documents: return False

            logger.info(f"🔧 RAG: Creating embeddings for {len(documents)} chunks...")
            self.vector_store = await FAISS.afrom_texts(documents, self.embeddings, metadatas=metadatas)
            return True

        except Exception as e:
            logger.error(f"❌ RAG: Index building failed: {e}")
            return False

    def save_index(self, index_path: Path):
        if not self.vector_store: raise ValueError("Vector store not initialized.")
        index_path.parent.mkdir(parents=True, exist_ok=True)
        self.vector_store.save_local(str(index_path))
        logger.info(f"💾 RAG: Index saved to {index_path}")

    def load_index(self, index_path: Path):
        if not index_path.exists(): raise FileNotFoundError(f"RAG index not found at {index_path}")
        self.vector_store = FAISS.load_local(str(index_path), self.embeddings, allow_dangerous_deserialization=True)
        logger.info(f"📚 RAG: Index loaded from {index_path}")

    async def query_codebase(self, query: str, k: int = 5) -> Dict[str, Any]:
        """Queries the loaded codebase index using RAG."""
        try:
            if not self.vector_store: return {"error": "No RAG index loaded."}

            docs = await self.vector_store.asimilarity_search(query, k=k)
            context_text = "\n\n---\n\n".join([f"**Source File: {doc.metadata['source']}**\n```\n{doc.page_content}\n```" for doc in docs])

            prompt = f"""
            You are an expert AI programming assistant. Based on the following relevant code snippets retrieved from a large codebase, provide a clear and detailed answer to the user's question. 
            Reference the source files where appropriate using markdown formatting (e.g., `filename.py`).

            **Retrieved Code Snippets:**
            {context_text}

            **User's Question:** {query}

            **Your Answer:**
            """
            response = await self.gemini_model.ainvoke(prompt)

            return {
                "query": query, "answer": response.content,
                "sources": sorted(list(set(doc.metadata["source"] for doc in docs))) # Return the clean relative paths
            }
        except Exception as e:
            logger.error(f"❌ RAG query failed: {e}")
            return {"error": str(e)}