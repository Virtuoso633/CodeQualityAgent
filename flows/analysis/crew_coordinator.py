"""
CrewAI-based multi-agent coordination for comprehensive code analysis
"""
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.core.base_analyzer import get_base_analyzer
from agents.specialized.security_agent import get_security_agent
from agents.specialized.performance_agent import get_performance_agent
from config.settings import settings

logger = logging.getLogger(__name__)

class CodeQualityCrewCoordinator:
    """Coordinates multiple specialized agents using CrewAI"""
    
    def __init__(self):
        """Initialize CrewAI coordinator with Gemini models"""
        self.gemini_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.gemini_api_key,
            temperature=0.1
        )
        
        self.complex_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro", 
            google_api_key=settings.gemini_api_key,
            temperature=0.1
        )
        
        # Initialize specialized agents
        self.base_analyzer = get_base_analyzer()
        self.security_agent = get_security_agent()
        self.performance_agent = get_performance_agent()
        
        # Create CrewAI agents
        self.agents = self._create_crew_agents()
        
    def _create_crew_agents(self) -> Dict[str, Agent]:
        """Create specialized CrewAI agents"""
        
        # Code Architecture Analyst Agent
        architecture_agent = Agent(
            role="Code Architecture Analyst",
            goal="Analyze code structure, design patterns, and architectural quality",
            backstory="""You are an expert software architect with deep knowledge of design patterns, 
            SOLID principles, and code organization. You analyze codebases to identify architectural 
            strengths and weaknesses, suggest improvements, and ensure maintainable code structure.""",
            #llm=self.gemini_model,
            llm="gemini/gemini-2.5-flash",
            verbose=True,
            allow_delegation=False
        )
        
        # Security Specialist Agent  
        security_specialist = Agent(
            role="Security Specialist", 
            goal="Identify security vulnerabilities and provide remediation guidance",
            backstory="""You are a cybersecurity expert specializing in secure coding practices.
            You identify OWASP Top 10 vulnerabilities, analyze potential attack vectors, and provide
            specific, actionable security recommendations with code examples.""",
            #llm=self.complex_model,
            llm="gemini/gemini-2.5-pro",
            verbose=True,
            allow_delegation=False
        )
        
        # Performance Optimization Expert
        performance_expert = Agent(
            role="Performance Optimization Expert",
            goal="Analyze performance bottlenecks and suggest optimizations", 
            backstory="""You are a performance engineering expert with deep knowledge of algorithmic
            complexity, memory optimization, and language-specific performance patterns. You identify
            bottlenecks and provide concrete optimization strategies.""",
            llm="gemini/gemini-2.5-pro",
            verbose=True,
            allow_delegation=False
        )
        
        # Quality Assurance Reviewer
        qa_reviewer = Agent(
            role="Quality Assurance Reviewer",
            goal="Synthesize findings and create comprehensive quality reports",
            backstory="""You are a senior QA engineer who synthesizes technical findings from multiple
            specialists into actionable, prioritized reports. You understand developer workflows and 
            create practical recommendations that teams can implement.""",
            llm="gemini/gemini-2.5-pro",
            verbose=True,
            allow_delegation=False
        )
        
        return {
            "architecture": architecture_agent,
            "security": security_specialist, 
            "performance": performance_expert,
            "qa_reviewer": qa_reviewer
        }
    
    def _create_analysis_tasks(self, code_content: str, file_path: str, language: str) -> List[Task]:
        """Create analysis tasks for each agent"""
        
        # Architecture Analysis Task
        architecture_task = Task(
            description=f"""
            Analyze the architectural quality of this {language} code from {file_path}:
            
            ```
            {code_content}
            ```
            
            Focus on:
            1. Design patterns usage and appropriateness
            2. SOLID principles adherence
            3. Code organization and modularity
            4. Separation of concerns
            5. Dependency management
            6. Testability and maintainability
            
            Provide specific architectural recommendations with examples.
            """,
            agent=self.agents["architecture"],
            expected_output="Detailed architectural analysis with specific improvement recommendations"
        )
        
        # Security Analysis Task
        security_task = Task(
            description=f"""
            Perform comprehensive security analysis of this {language} code from {file_path}:
            
            ```
            {code_content}
            ```
            
            Analyze for:
            1. OWASP Top 10 vulnerabilities
            2. Input validation issues
            3. Authentication and authorization flaws
            4. Data exposure risks
            5. Cryptographic weaknesses
            6. Language-specific security patterns
            
            Provide severity ratings and specific remediation steps.
            """,
            agent=self.agents["security"],
            expected_output="Security vulnerability report with remediation guidance"
        )
        
        # Performance Analysis Task
        performance_task = Task(
            description=f"""
            Analyze performance characteristics of this {language} code from {file_path}:
            
            ```
            {code_content}
            ```
            
            Evaluate:
            1. Algorithmic complexity (Big O analysis)
            2. Memory usage patterns
            3. I/O efficiency
            4. Concurrency opportunities
            5. Language-specific optimizations
            6. Scalability concerns
            
            Provide performance scores and optimization strategies.
            """,
            agent=self.agents["performance"],
            expected_output="Performance analysis with optimization recommendations"
        )
        
        # QA Review Task (depends on other tasks)
        qa_task = Task(
            description=f"""
            Synthesize the architectural, security, and performance analyses into a comprehensive
            quality report for {file_path}.
            
            Create:
            1. Executive summary with overall quality score (1-10)
            2. Prioritized list of issues (Critical/High/Medium/Low)
            3. Quick wins vs. long-term improvements
            4. Specific action items with code examples
            5. Risk assessment and business impact
            6. Implementation timeline recommendations
            
            Format as a professional code review report.
            """,
            agent=self.agents["qa_reviewer"],
            expected_output="Comprehensive quality report with prioritized recommendations",
            context=[architecture_task, security_task, performance_task]
        )
        
        return [architecture_task, security_task, performance_task, qa_task]
    
    async def analyze_file_with_crew(self, file_path: str, code_content: str, language: str) -> Dict[str, Any]:
        """Analyze file using coordinated crew of agents"""
        try:
            logger.info(f"🚀 Starting CrewAI analysis for {file_path}")
            
            # Create tasks
            tasks = self._create_analysis_tasks(code_content, file_path, language)
            
            # Create and run crew
            crew = Crew(
                agents=list(self.agents.values()),
                tasks=tasks,
                process=Process.sequential,  # Run tasks in sequence
                verbose=True
            )
            
            # Execute crew analysis
            # Note: CrewAI.kickoff() is synchronous, but we can wrap it
            def run_crew():
                return crew.kickoff()
            
            # Run in thread to avoid blocking
            import concurrent.futures
            loop = asyncio.get_event_loop()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                crew_results = await loop.run_in_executor(executor, run_crew)
            
            # Structure results
            analysis_result = {
                "file_path": file_path,
                "language": language,
                "analysis_type": "crew_coordinated",
                "crew_results": crew_results,
                "task_outputs": {
                    "architecture": tasks[0].output if hasattr(tasks[0], 'output') else None,
                    "security": tasks[1].output if hasattr(tasks[1], 'output') else None,
                    "performance": tasks[2].output if hasattr(tasks[2], 'output') else None,
                    "qa_report": tasks[3].output if hasattr(tasks[3], 'output') else None
                },
                "timestamp": asyncio.get_event_loop().time(),
                "agents_used": list(self.agents.keys())
            }
            
            logger.info(f"✅ CrewAI analysis completed for {file_path}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ CrewAI analysis failed for {file_path}: {e}")
            return {
                "file_path": file_path,
                "error": str(e),
                "analysis_type": "crew_failed"
            }

# Global coordinator instance
crew_coordinator = None

def get_crew_coordinator() -> CodeQualityCrewCoordinator:
    """Get or create global CrewAI coordinator instance"""
    global crew_coordinator
    if crew_coordinator is None:
        crew_coordinator = CodeQualityCrewCoordinator()
    return crew_coordinator
