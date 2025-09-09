"""
RAG-based analyzer for large codebase understanding
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
        """Initialize RAG analyzer with Google embeddings and Gemini models"""
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",  # auto-resolves in new versions
            google_api_key=settings.gemini_api_key
        )

        self.gemini_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.gemini_api_key,
            temperature=0.1
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

        self.vector_store: Optional[FAISS] = None
        self.codebase_metadata: Dict[str, Any] = {}

    # -------------------- File & Language Utilities -------------------- #
    def _collect_code_files(self, directory_path: str) -> List[Path]:
        """Collect all supported code files from a directory"""
        from config.settings import SUPPORTED_LANGUAGES

        dir_path = Path(directory_path)
        if dir_path.is_file():
            return [dir_path]

        extensions = [ext for lang in SUPPORTED_LANGUAGES.values() for ext in lang["extensions"]]
        code_files = [f for ext in extensions for f in dir_path.rglob(f"*{ext}")]
        return sorted(list(set(code_files)))

    def _detect_language(self, file_path: str) -> str:
        """Detect language from file extension"""
        from config.settings import SUPPORTED_LANGUAGES

        ext = Path(file_path).suffix.lower()
        for lang, config in SUPPORTED_LANGUAGES.items():
            if ext in config["extensions"]:
                return lang
        return "unknown"

    # -------------------- RAG Indexing -------------------- #
    async def build_codebase_index(self, codebase_path: str, max_files: int = 50) -> Dict[str, Any]:
        """Build RAG index for large codebase"""
        try:
            logger.info(f"🔍 Building RAG index for {codebase_path}")
            code_files = self._collect_code_files(codebase_path)

            if len(code_files) > 100:
                logger.info(f"📚 Large codebase detected: {len(code_files)} files")

            documents = []
            metadatas = []

            for file_path in code_files[:max_files]:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    chunks = self.text_splitter.split_text(content)
                    for idx, chunk in enumerate(chunks):
                        documents.append(chunk)
                        metadatas.append({
                            "file_path": str(file_path),
                            "chunk_id": idx,
                            "file_size": len(content),
                            "language": self._detect_language(file_path)
                        })
                except Exception as e:
                    logger.warning(f"⚠️ Skipping file {file_path}: {e}")
                    continue

            logger.info(f"🔧 Creating embeddings for {len(documents)} chunks...")
            self.vector_store = await FAISS.afrom_texts(documents, self.embeddings, metadatas=metadatas)

            self.codebase_metadata = {
                "total_files": len(code_files),
                "indexed_files": len(set(m["file_path"] for m in metadatas)),
                "total_chunks": len(documents),
                "languages": list(set(m["language"] for m in metadatas if m["language"]))
            }

            logger.info(f"✅ RAG index built: {len(documents)} chunks from {self.codebase_metadata['indexed_files']} files")
            return self.codebase_metadata

        except Exception as e:
            logger.error(f"❌ RAG index building failed: {e}")
            return {"error": str(e)}

    # -------------------- RAG Query -------------------- #
    async def query_codebase(self, query: str, k: int = 5) -> Dict[str, Any]:
        """Query the codebase using RAG"""
        try:
            if not self.vector_store:
                return {"error": "No RAG index built. Please build index first."}

            # Retrieve top-k relevant chunks
            docs = await self.vector_store.asimilarity_search(query, k=k)

            context_text = "\n\n".join([
                f"File: {doc.metadata['file_path']}\n{doc.page_content}" for doc in docs
            ])

            prompt = f"""
            Based on the following code snippets from the codebase, answer the user's question:

            CODEBASE CONTEXT:
            {context_text}

            USER QUESTION: {query}

            Provide a detailed answer referencing specific files and code sections.
            Include suggestions for improvements if relevant.
            """

            response = await self.gemini_model.ainvoke([{"role": "user", "content": prompt}])

            return {
                "query": query,
                "answer": response.content,
                "retrieved_chunks": len(docs),
                "sources": [doc.metadata["file_path"] for doc in docs],
                "model_used": "gemini-2.5-pro-rag"
            }

        except Exception as e:
            logger.error(f"❌ RAG query failed: {e}")
            return {"error": str(e)}
