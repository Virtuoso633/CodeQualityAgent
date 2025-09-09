"""
Interactive Q&A system for codebase conversations
"""
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferWindowMemory
from config.settings import settings
from agents.core.base_analyzer import get_base_analyzer

logger = logging.getLogger(__name__)

class InteractiveQASystem:
    """Interactive Q&A system for codebase conversations"""
    
    def __init__(self):
        """Initialize Q&A system with Gemini models"""
        self.gemini_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",  # Use Pro for better reasoning
            google_api_key=settings.gemini_api_key,
            temperature=0.2  # Slightly higher for more conversational responses
        )
        
        self.base_analyzer = get_base_analyzer()
        self.conversation_memory = ConversationBufferWindowMemory(
            k=10,  # Remember last 10 exchanges
            return_messages=True
        )
        
        # Codebase context
        self.codebase_context = {}
        self.current_codebase_path = None
        
    async def load_codebase_context(self, codebase_path: str) -> Dict[str, Any]:
        """Load and analyze codebase to create context for Q&A"""
        try:
            logger.info(f"📚 Loading codebase context from {codebase_path}")
            
            target_path = Path(codebase_path)
            if not target_path.exists():
                return {"error": f"Path not found: {codebase_path}"}
            
            # Analyze codebase structure
            if target_path.is_file():
                # Single file analysis
                language = self.base_analyzer.detect_language(codebase_path)
                code_content = self.base_analyzer.read_code_file(codebase_path)
                
                context = {
                    "type": "single_file",
                    "path": codebase_path,
                    "language": language,
                    "content": code_content,
                    "size": len(code_content),
                    "lines": code_content.count('\n') + 1
                }
                
            else:
                # Directory analysis
                directory_analysis = await self.base_analyzer.analyze_directory(codebase_path, "simple")
                
                # Create structured context
                context = {
                    "type": "directory",
                    "path": codebase_path,
                    "total_files": directory_analysis.get("total_files_found", 0),
                    "analyzed_files": directory_analysis.get("files_analyzed", 0),
                    "languages": directory_analysis.get("languages_detected", []),
                    "file_details": {}
                }
                
                # Store individual file contents (limited)
                for result in directory_analysis.get("results", [])[:5]:  # Limit to first 5 files
                    if "error" not in result:
                        file_path = result["file_path"]
                        context["file_details"][file_path] = {
                            "language": result["language"],
                            "size": result["file_size"],
                            "content_preview": self.base_analyzer.read_code_file(file_path)[:1000]  # First 1000 chars
                        }
            
            self.codebase_context = context
            self.current_codebase_path = codebase_path
            
            logger.info(f"✅ Codebase context loaded: {context['type']} with {len(context.get('file_details', {}))} files")
            return context
            
        except Exception as e:
            logger.error(f"❌ Failed to load codebase context: {e}")
            return {"error": str(e)}
    
    def _create_system_prompt(self) -> str:
        """Create system prompt with codebase context"""
        if not self.codebase_context:
            return """You are a helpful code analysis assistant. You can answer questions about code quality, 
            security, performance, and best practices. Please be specific and provide actionable advice."""
        
        context_info = self.codebase_context
        
        if context_info["type"] == "single_file":
            system_prompt = f"""
            You are an expert code analysis assistant with deep knowledge of the following codebase:
            
            **CODEBASE CONTEXT:**
            - File: {context_info['path']}
            - Language: {context_info['language']}
            - Size: {context_info['size']} bytes ({context_info['lines']} lines)
            
            **CODE CONTENT:**
            ```
            {context_info['content']}
            ```
            
            Answer questions about this code with specific references to line numbers, functions, and implementation details.
            Provide actionable advice for improvements, security fixes, performance optimizations, and best practices.
            """
            
        else:
            file_list = '\n'.join([f"- {path} ({details['language']}, {details['size']} bytes)" 
                                 for path, details in context_info.get('file_details', {}).items()])
            
            system_prompt = f"""
            You are an expert code analysis assistant with knowledge of the following codebase:
            
            **CODEBASE CONTEXT:**
            - Directory: {context_info['path']}
            - Total Files: {context_info['total_files']}
            - Languages: {', '.join(context_info['languages'])}
            - Files Analyzed: {context_info['analyzed_files']}
            
            **FILE STRUCTURE:**
            {file_list}
            
            Answer questions about this codebase, referencing specific files and their relationships.
            Provide architectural insights, security recommendations, and performance guidance.
            """
        
        return system_prompt
            

    async def ask_question(self, question: str, context_override: Optional[str] = None) -> Dict[str, Any]:
        """Ask a question about the codebase, with optional direct context override."""
        try:
            # Create system prompt based on available context
            if context_override:
                # Use the direct context string provided by the API
                system_prompt = f"""
                You are an expert code analysis assistant. A user has analyzed their codebase and received the following summary. 
                Answer their follow-up question based *only* on this summary.

                ANALYSIS SUMMARY:
                {context_override}
                
                Based on the summary above, answer the user's question. Be helpful and refer to the data provided.
                """
            elif not self.codebase_context:
                return {
                    "error": "No codebase loaded. Please load a codebase first using the 'chat' command with a path."
                }
            else:
                # This path is used by the CLI
                system_prompt = self._create_system_prompt()

            # The rest of the function remains the same...
            memory_messages = self.conversation_memory.chat_memory.messages
            messages = [SystemMessage(content=system_prompt)]
            messages.extend(memory_messages[-10:])
            messages.append(HumanMessage(content=question))
            
            response = await self.gemini_model.ainvoke(messages)
            
            self.conversation_memory.chat_memory.add_user_message(question)
            self.conversation_memory.chat_memory.add_ai_message(response.content)
            
            return {
                "question": question,
                "answer": response.content,
                "codebase": self.current_codebase_path or "Web Analysis",
                "timestamp": asyncio.get_event_loop().time(),
                "model_used": "gemini-2.5-pro"
            }
            
        except Exception as e:
            logger.error(f"❌ Q&A failed: {e}")
            return {
                "question": question,
                "error": str(e),
                "codebase": self.current_codebase_path
            }
    
    async def start_interactive_session(self, codebase_path: str):
        """Start interactive chat session"""
        try:
            from rich.console import Console
            from rich.panel import Panel
            
            console = Console()
            
            # Load codebase
            console.print(f"📚 Loading codebase: {codebase_path}", style="bold blue")
            context = await self.load_codebase_context(codebase_path)
            
            if "error" in context:
                console.print(f"❌ Error loading codebase: {context['error']}", style="bold red")
                return
            
            # Show context info
            if context["type"] == "single_file":
                console.print(Panel(
                    f"📄 **File**: {context['path']}\n"
                    f"🔤 **Language**: {context['language']}\n"
                    f"📏 **Size**: {context['size']} bytes ({context['lines']} lines)",
                    title="Codebase Loaded",
                    style="green"
                ))
            else:
                console.print(Panel(
                    f"📁 **Directory**: {context['path']}\n"
                    f"📄 **Files**: {context['total_files']} found, {context['analyzed_files']} analyzed\n"
                    f"🔤 **Languages**: {', '.join(context['languages'])}",
                    title="Codebase Loaded", 
                    style="green"
                ))
            
            console.print("\n💬 **Interactive Q&A Session Started!**", style="bold cyan")
            console.print("Ask questions about your code. Type 'exit' to quit.\n", style="dim")
            
            # Interactive loop
            while True:
                try:
                    # Get user input
                    question = input("🤔 Your Question: ").strip()
                    
                    if question.lower() in ['exit', 'quit', 'bye']:
                        console.print("👋 Goodbye! Happy coding!", style="bold green")
                        break
                    
                    if not question:
                        continue
                    
                    # Get answer
                    console.print("🤖 Thinking...", style="dim")
                    result = await self.ask_question(question)
                    
                    if "error" in result:
                        console.print(f"❌ Error: {result['error']}", style="bold red")
                    else:
                        console.print(Panel(
                            result["answer"],
                            title="AI Assistant Response",
                            style="blue"
                        ))
                    
                    console.print()  # Add spacing
                    
                except KeyboardInterrupt:
                    console.print("\n👋 Session interrupted. Goodbye!", style="bold yellow")
                    break
                except Exception as e:
                    console.print(f"❌ Session error: {e}", style="bold red")
                    break
            
        except Exception as e:
            logger.error(f"❌ Interactive session failed: {e}")
            raise

# Global Q&A system instance
qa_system = None

def get_qa_system() -> InteractiveQASystem:
    """Get or create global Q&A system instance"""
    global qa_system
    if qa_system is None:
        qa_system = InteractiveQASystem()
    return qa_system
