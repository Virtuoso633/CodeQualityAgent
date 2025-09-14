# In agents/specialized/architecture_agent.py

"""
Specialized Architecture Analysis Agent
"""
import json
from typing import Dict, List, Any
import logging
from models.gemini.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)

class ArchitectureAnalysisAgent:
    """Specialized agent for generating high-level architecture diagrams in Mermaid syntax."""
    
    def __init__(self):
        self.gemini_client = get_gemini_client()

    async def analyze_codebase_structure(self, file_paths: List[str]) -> str:
        """
        Analyzes a list of file paths to generate a Mermaid diagram of the architecture.
        """
        # Create a simplified text representation of the directory structure
        file_tree = self._generate_file_tree_string(file_paths)

        prompt = f"""
        You are an expert software architect. Based on the following file structure of a codebase, generate a high-level component architecture diagram.

        FILE STRUCTURE:
        ```
        {file_tree}
        ```

        Your task is to identify the main components (e.g., "Frontend UI", "Backend API", "Data Models", "AI Agents", "CLI") and the relationships between them.

        Respond ONLY with a valid Mermaid syntax string for a top-down graph diagram (`graph TD`).
        Do not include any explanation, markdown formatting like ```mermaid, or any other text.
        The diagram should be simple and clear.

        Example of a valid response:
        graph TD
            A[User Interface] --> B[API Gateway]
            B --> C[Authentication Service]
            B --> D[Code Analysis Service]
            D --> E[AI Agents]
            E --> F[Gemini LLM]
        """
        try:
            response_content = await self.gemini_client.analyze_code_simple("", "architecture", prompt_override=prompt)
            
            # ROBUST FIX: The LLM often adds explanatory text before the code, even when told not to.
            # We must find the start of the graph ("graph TD") and take everything *after* it.
            
            graph_start_index = response_content.find("graph TD")
            
            if graph_start_index == -1:
                # The LLM failed to return a graph at all.
                logger.warning(f"Architecture agent did not find 'graph TD' in LLM response: {response_content}")
                return "" # Return an empty string. Your frontend 'if' check will now correctly fail and show the error.

            # We found the start of the graph. Take everything from that point on.
            mermaid_code = response_content[graph_start_index:]
            
            # Now, just clean up any trailing markdown fences the LLM might have added at the end.
            mermaid_code = mermaid_code.replace("```", "").strip()
            
            return mermaid_code

        except Exception as e:
            logger.error(f"❌ Architecture analysis failed: {e}")
            return "graph TD\n    A[Error] --> B[Could not generate architecture diagram]"

    def _generate_file_tree_string(self, file_paths: List[str], max_files: int = 75) -> str:
        """Creates a simplified string representation of the file tree."""
        if not file_paths:
            return "No files found."
        
        output = []
        for path in sorted(file_paths)[:max_files]:
            output.append(path)
        
        if len(file_paths) > max_files:
            output.append(f"\n... and {len(file_paths) - max_files} more files.")
            
        return "\n".join(output)

# Singleton instance
architecture_agent = None

def get_architecture_agent() -> ArchitectureAnalysisAgent:
    global architecture_agent
    if architecture_agent is None:
        architecture_agent = ArchitectureAnalysisAgent()
    return architecture_agent
