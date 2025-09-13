"""
CrewAI-based multi-agent coordination for FINAL report synthesis - CORRECTED VERSION
"""
import asyncio
from typing import Dict, List, Any
import logging
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings

logger = logging.getLogger(__name__)

class CodeQualityCrewCoordinator:
    """Coordinates a crew of AI agents to synthesize technical findings into a high-level summary."""

    def __init__(self):
        """Initializes the coordinator with the LLM for the agents."""
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", # Use the powerful model for synthesis
                google_api_key=settings.gemini_api_key,
                temperature=0.3 # Allow for slightly more creative summarization
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini model for CrewAI: {e}")
            raise

    async def generate_executive_summary(self, all_issues_json: str) -> str:
        """
        Uses a CrewAI team to analyze a JSON string of all technical findings
        and produce a high-level, business-focused executive summary.
        """
        try:
            logger.info("🚀 Kicking off CrewAI for executive summary generation...")
            
            # Define the agents for the crew
            lead_engineer = Agent(
                role="Principal Software Engineer",
                goal="Analyze a JSON list of code quality issues to identify the most critical technical patterns, risks, and recurring problems.",
                backstory="You are a highly experienced engineering leader. Your expertise is in looking at raw security and performance data and quickly identifying the systemic root causes and highest-priority technical themes.",
                llm="gemini/gemini-2.5-flash",
                verbose=True
            )
            
            product_manager = Agent(
                role="Senior Product Manager",
                goal="Translate the lead engineer's technical findings into a concise, business-focused executive summary for stakeholders.",
                backstory="You are a product leader who excels at communicating complex technical challenges and their direct impact on the business. You focus on risk, user impact, and future development velocity.",
                llm="gemini/gemini-2.5-flash",
                verbose=True
            )

            # Define the tasks for the agents
            analysis_task = Task(
                description=(
                    "Analyze the following JSON data which contains all security and performance issues found in a codebase. "
                    "Your task is to identify the top 3-5 most critical themes or recurring problems. "
                    "Focus on systemic risks (e.g., 'consistent lack of input validation,' 'widespread use of inefficient data structures') rather than just listing individual bugs. "
                    f"Here is the raw data:\n\nDATA:\n{all_issues_json}"
                ),
                agent=lead_engineer,
                expected_output="A bulleted list summarizing the most critical, high-level technical themes and underlying risks present in the code."
            )
            
            summary_task = Task(
                description=(
                    "Using the lead engineer's analysis of the critical technical themes, write a concise, high-level executive summary in markdown format. "
                    "The summary should be easy for a non-technical manager to understand. "
                    "Start with a title 'Executive Summary'. Then provide a brief overview of the codebase's health. "
                    "Finally, create a prioritized, numbered list of the top 3 recommended actions for the development team to take next, explaining the business impact of each."
                ),
                agent=product_manager,
                context=[analysis_task], # This task depends on the output of the analysis task
                expected_output="A professional, markdown-formatted executive summary with a title, a brief overview, and a prioritized list of 3 actionable recommendations."
            )
            
            # Assemble and run the crew
            crew = Crew(
                agents=[lead_engineer, product_manager],
                tasks=[analysis_task, summary_task],
                process=Process.sequential
            )
            
            def run_crew():
                # Encapsulate the synchronous kickoff call
                return crew.kickoff()

            # Run the synchronous CrewAI kickoff in a separate thread to avoid blocking asyncio event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, run_crew)
            
            logger.info("✅ CrewAI executive summary generated successfully.")
            return str(result)

        except Exception as e:
            logger.error(f"❌ CrewAI analysis failed: {e}")
            return "An error occurred while generating the AI summary. Please check the backend logs."

# Global instance for singleton pattern
crew_coordinator = None

def get_crew_coordinator() -> CodeQualityCrewCoordinator:
    """Provides a global singleton instance of the CodeQualityCrewCoordinator."""
    global crew_coordinator
    if crew_coordinator is None:
        crew_coordinator = CodeQualityCrewCoordinator()
    return crew_coordinator