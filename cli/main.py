"""
CLI interface for CodeQualityAgent
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import settings
from agents.core.base_analyzer import get_base_analyzer
from models.gemini.gemini_client import get_gemini_client
from agents.specialized.security_agent import get_security_agent
from agents.specialized.performance_agent import get_performance_agent
from flows.analysis.crew_coordinator import get_crew_coordinator
from flows.interactive.qa_system import get_qa_system
from tools.analyzers.rag_analyzer import RAGCodeAnalyzer
from tools.analyzers.comprehensive_scanner import ComprehensiveCodebaseScanner

# Initialize
app = typer.Typer(help="CodeQualityAgent - AI-powered code analysis")
console = Console()

@app.command()
def test_connection():
    """Test Gemini API connection"""
    console.print("🔌 Testing Gemini API connection...", style="bold blue")
    
    async def _test():
        try:
            client = get_gemini_client()
            success = await client.test_connection()
            
            if success:
                console.print("✅ Gemini API connection successful!", style="bold green")
                return True
            else:
                console.print("❌ Gemini API connection failed", style="bold red")
                return False
                
        except Exception as e:
            console.print(f"❌ Connection test error: {e}", style="bold red")
            return False
    
    # Run async function
    success = asyncio.run(_test())
    if not success:
        console.print("💡 Check your GEMINI_API_KEY in .env file", style="yellow")
        raise typer.Exit(1)

@app.command()
def analyze(
    path: str = typer.Argument(..., help="Path to code file or directory"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Use detailed analysis"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save results to file")
):
    """Analyze code file or directory"""
    
    analysis_type = "detailed" if detailed else "simple"
    
    console.print(f"🚀 Starting {analysis_type} analysis of: {path}", style="bold cyan")
    
    async def _analyze():
        try:
            analyzer = get_base_analyzer()
            
            # Check if path exists
            target_path = Path(path)
            if not target_path.exists():
                console.print(f"❌ Path not found: {path}", style="bold red")
                return
            
            # Analyze
            if target_path.is_file():
                console.print("📄 Analyzing single file...", style="blue")
                result = await analyzer.analyze_single_file(path, analysis_type)
            else:
                console.print("📁 Analyzing directory...", style="blue")
                result = await analyzer.analyze_directory(path, analysis_type)
            
            # Display results
            display_results(result, analysis_type)
            
            # Save to file if requested
            if output:
                save_results(result, output)
                console.print(f"💾 Results saved to: {output}", style="green")
            
        except Exception as e:
            console.print(f"❌ Analysis failed: {e}", style="bold red")
            raise typer.Exit(1)
    
    # Run analysis
    asyncio.run(_analyze())

@app.command()
def security(
    path: str = typer.Argument(..., help="Path to code file"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save results to file")
):
    """Run specialized security analysis"""
    
    console.print(f"🔒 Starting security analysis of: {path}", style="bold red")
    
    async def _security_analyze():
        try:
            security_agent = get_security_agent()
            analyzer = get_base_analyzer()
            
            # Check if file exists and get details
            target_path = Path(path)
            if not target_path.exists():
                console.print(f"❌ File not found: {path}", style="bold red")
                return
            
            if not target_path.is_file():
                console.print("❌ Security analysis currently supports single files only", style="bold red")
                return
            
            # Get language and code content
            language = analyzer.detect_language(path)
            if not language:
                console.print("❌ Unsupported file type for security analysis", style="bold red")
                return
            
            code_content = analyzer.read_code_file(path)
            
            # Run security analysis
            result = await security_agent.analyze_file_security(path, code_content, language)
            
            # Display results
            display_security_results(result)
            
            # Save if requested
            if output:
                save_results(result, output)
                console.print(f"💾 Security results saved to: {output}", style="green")
            
        except Exception as e:
            console.print(f"❌ Security analysis failed: {e}", style="bold red")
            raise typer.Exit(1)
    
    asyncio.run(_security_analyze())

@app.command()
def performance(
    path: str = typer.Argument(..., help="Path to code file"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save results to file")
):
    """Run specialized performance analysis"""
    
    console.print(f"⚡ Starting performance analysis of: {path}", style="bold yellow")
    
    async def _performance_analyze():
        try:
            performance_agent = get_performance_agent()
            analyzer = get_base_analyzer()
            
            # Check if file exists and get details
            target_path = Path(path)
            if not target_path.exists():
                console.print(f"❌ File not found: {path}", style="bold red")
                return
            
            if not target_path.is_file():
                console.print("❌ Performance analysis currently supports single files only", style="bold red")
                return
            
            # Get language and code content
            language = analyzer.detect_language(path)
            if not language:
                console.print("❌ Unsupported file type for performance analysis", style="bold red")
                return
            
            code_content = analyzer.read_code_file(path)
            
            # Run performance analysis
            result = await performance_agent.analyze_file_performance(path, code_content, language)
            
            # Display results
            display_performance_results(result)
            
            # Save if requested
            if output:
                save_results(result, output)
                console.print(f"💾 Performance results saved to: {output}", style="green")
            
        except Exception as e:
            console.print(f"❌ Performance analysis failed: {e}", style="bold red")
            raise typer.Exit(1)
    
    asyncio.run(_performance_analyze())
    

@app.command()
def crew_analyze(
    path: str = typer.Argument(..., help="Path to code file"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save results to file")
):
    """Run comprehensive analysis using CrewAI multi-agent coordination"""
    
    console.print(f"🚀 Starting CrewAI multi-agent analysis of: {path}", style="bold magenta")
    
    async def _crew_analyze():
        try:
            crew_coordinator = get_crew_coordinator()
            analyzer = get_base_analyzer()
            
            # Check if file exists
            target_path = Path(path)
            if not target_path.exists():
                console.print(f"❌ File not found: {path}", style="bold red")
                return
            
            if not target_path.is_file():
                console.print("❌ CrewAI analysis currently supports single files only", style="bold red")
                return
            
            # Get language and code content
            language = analyzer.detect_language(path)
            if not language:
                console.print("❌ Unsupported file type", style="bold red")
                return
                
            code_content = analyzer.read_code_file(path)
            
            # Run CrewAI analysis
            with console.status("🤖 Running multi-agent analysis...", spinner="dots"):
                result = await crew_coordinator.analyze_file_with_crew(path, code_content, language)
            
            # Display results
            display_crew_results(result)
            
            # Save if requested
            if output:
                save_results(result, output)
                console.print(f"💾 CrewAI results saved to: {output}", style="green")
            
        except Exception as e:
            console.print(f"❌ CrewAI analysis failed: {e}", style="bold red")
            raise typer.Exit(1)
    
    asyncio.run(_crew_analyze())

@app.command()
def chat(
    path: str = typer.Argument(..., help="Path to code file or directory")
):
    """Start interactive Q&A session about your codebase"""
    
    console.print(f"💬 Starting interactive chat about: {path}", style="bold cyan")
    
    async def _start_chat():
        try:
            qa_system = get_qa_system()
            await qa_system.start_interactive_session(path)
            
        except Exception as e:
            console.print(f"❌ Chat session failed: {e}", style="bold red")
            raise typer.Exit(1)
    
    asyncio.run(_start_chat())
    
# Add import
from tools.analyzers.rag_analyzer import RAGCodeAnalyzer

@app.command()
def rag_build(
    path: str = typer.Argument(..., help="Path to large codebase directory")
):
    """Build RAG index for large codebase analysis"""
    
    console.print(f"🔍 Building RAG index for: {path}", style="bold purple")
    
    async def _build_rag():
        try:
            rag_analyzer = RAGCodeAnalyzer()
            
            with console.status("🔧 Building RAG index...", spinner="dots"):
                metadata = await rag_analyzer.build_codebase_index(path)
            
            if "error" in metadata:
                console.print(f"❌ RAG build failed: {metadata['error']}", style="bold red")
                return
            
            console.print(Panel(
                f"📚 **Codebase**: {path}\n"
                f"📄 **Total Files**: {metadata['total_files']}\n"
                f"🔍 **Indexed Files**: {metadata['indexed_files']}\n" 
                f"📝 **Total Chunks**: {metadata['total_chunks']}\n"
                f"🔤 **Languages**: {', '.join(metadata['languages'])}",
                title="RAG Index Built Successfully",
                style="purple"
            ))
            
        except Exception as e:
            console.print(f"❌ RAG build failed: {e}", style="bold red")
            raise typer.Exit(1)
    
    asyncio.run(_build_rag())

@app.command()
def rag_query(
    query: str = typer.Argument(..., help="Query about the codebase"),
    path: str = typer.Option(".", help="Codebase path (must build index first)")
):
    """Query large codebase using RAG"""
    
    console.print(f"💭 Querying codebase: {query}", style="bold purple")
    
    async def _rag_query():
        try:
            rag_analyzer = RAGCodeAnalyzer()
            
            # Build index if not exists (for demo)
            await rag_analyzer.build_codebase_index(path)
            
            with console.status("🔍 Searching codebase...", spinner="dots"):
                result = await rag_analyzer.query_codebase(query)
            
            if "error" in result:
                console.print(f"❌ Query failed: {result['error']}", style="bold red")
                return
            
            console.print(Panel(
                result["answer"],
                title=f"RAG Query Result ({result['retrieved_chunks']} sources)",
                style="blue"
            ))
            
            console.print(f"\n📄 **Sources**: {', '.join(set(result['sources']))}", style="dim")
            
        except Exception as e:
            console.print(f"❌ RAG query failed: {e}", style="bold red")
            raise typer.Exit(1)
    
    asyncio.run(_rag_query())


def display_crew_results(result: dict):
    """Display CrewAI analysis results"""
    if "error" in result:
        console.print(Panel(f"❌ Error: {result['error']}", title="CrewAI Analysis Error", style="red"))
        return
    
    console.print(Panel(
        f"🚀 **File**: {result['file_path']}\n"
        f"🔤 **Language**: {result['language']}\n"
        f"🤖 **Analysis Type**: Multi-Agent Crew Coordination\n"
        f"👥 **Agents Used**: {', '.join(result['agents_used'])}",
        title="CrewAI Analysis Summary",
        style="magenta"
    ))
    
    # Show task outputs
    task_outputs = result.get("task_outputs", {})
    
    for task_name, output in task_outputs.items():
        if output and str(output).strip():
            console.print(f"\n🤖 **{task_name.upper()} AGENT ANALYSIS:**")
            # Truncate long outputs for display
            content = str(output)
            if len(content) > 800:
                content = content[:800] + "..."
            console.print(Panel(content, style="dim"))
    
    # Show final crew results
    if result.get("crew_results"):
        console.print(Panel(
            str(result["crew_results"])[:1000] + "..." if len(str(result["crew_results"])) > 1000 else str(result["crew_results"]),
            title="Final Crew Coordination Report",
            style="green"
        ))

def display_security_results(result: dict):
    """Display security analysis results"""
    if "error" in result:
        console.print(Panel(f"❌ Error: {result['error']}", title="Security Analysis Error", style="red"))
        return
    
    # Show summary
    summary = result.get("summary", {})
    console.print(Panel(
        f"🔒 **File**: {result['file_path']}\n"
        f"🔤 **Language**: {result['language']}\n"
        f"🚨 **Risk Level**: {summary.get('risk_level', 'unknown').upper()}\n"
        f"🔍 **Pattern Matches**: {summary.get('total_pattern_matches', 0)}\n"
        f"📋 **Categories Found**: {', '.join(summary.get('categories_found', []))}",
        title="Security Analysis Summary",
        style="red"
    ))
    
    # Show pattern matches
    pattern_analysis = result.get("pattern_analysis", {})
    if pattern_analysis.get("pattern_matches"):
        for category, matches in pattern_analysis["pattern_matches"].items():
            console.print(f"\n🚨 **{category.upper().replace('_', ' ')}** ({len(matches)} issues):")
            for match in matches[:3]:  # Show first 3 matches
                console.print(f"   Line {match['line']}: {match['code']}", style="dim")
            if len(matches) > 3:
                console.print(f"   ... and {len(matches) - 3} more", style="dim")
    
    # Show detailed analysis (truncated)
    detailed = result.get("detailed_analysis", {})
    if detailed.get("detailed_analysis") and "error" not in detailed:
        content = detailed["detailed_analysis"]
        if len(content) > 500:
            content = content[:500] + "..."
        console.print(Panel(content, title="Detailed Security Analysis", style="blue"))

def display_performance_results(result: dict):
    """Display performance analysis results"""
    if "error" in result:
        console.print(Panel(f"❌ Error: {result['error']}", title="Performance Analysis Error", style="red"))
        return
    
    # Show summary
    summary = result.get("summary", {})
    console.print(Panel(
        f"⚡ **File**: {result['file_path']}\n"
        f"🔤 **Language**: {result['language']}\n"
        f"📊 **Performance Score**: {summary.get('performance_score', 0)}/10\n"
        f"🔍 **Total Issues**: {summary.get('total_issues', 0)}\n"
        f"🚨 **Critical Issues**: {summary.get('critical_issues', 0)}",
        title="Performance Analysis Summary",
        style="yellow"
    ))
    
    # Show severity breakdown
    severity = summary.get("severity_breakdown", {})
    if any(severity.values()):
        console.print(f"\n📈 **Issue Breakdown**:")
        for level, count in severity.items():
            if count > 0:
                console.print(f"   {level.capitalize()}: {count}", style="dim")
    
    # Show pattern matches
    pattern_analysis = result.get("pattern_analysis", {})
    if pattern_analysis.get("pattern_matches"):
        for category, matches in pattern_analysis["pattern_matches"].items():
            console.print(f"\n⚡ **{category.upper().replace('_', ' ')}** ({len(matches)} issues):")
            for match in matches[:3]:  # Show first 3 matches
                console.print(f"   Line {match['line']}: {match['code']} ({match['severity']})", style="dim")
            if len(matches) > 3:
                console.print(f"   ... and {len(matches) - 3} more", style="dim")
    
    # Show detailed analysis (truncated)  
    detailed = result.get("detailed_analysis", {})
    if detailed.get("detailed_analysis") and "error" not in detailed:
        content = detailed["detailed_analysis"]
        if len(content) > 500:
            content = content[:500] + "..."
        console.print(Panel(content, title="Detailed Performance Analysis", style="blue"))


def display_results(result: dict, analysis_type: str):
    """Display analysis results in a nice format"""
    
    if "error" in result:
        console.print(Panel(f"❌ Error: {result['error']}", title="Analysis Error", style="red"))
        return
    
    # Single file results
    if "file_path" in result and "result" in result:
        console.print(Panel(
            f"📄 **File**: {result['file_path']}\n"
            f"🔤 **Language**: {result['language']}\n" 
            f"📊 **Analysis**: {result['analysis_type']}\n"
            f"📏 **Size**: {result['file_size']} bytes",
            title="File Analysis Results",
            style="green"
        ))
        
        # Display the actual analysis
        if isinstance(result['result'], dict):
            if result['result'].get('content'):
                console.print(Panel(result['result']['content'], title="Analysis Details", style="blue"))
            else:
                console.print(Panel(str(result['result']), title="Analysis Details", style="blue"))
        else:
            console.print(Panel(str(result['result']), title="Analysis Details", style="blue"))
    
    # Directory results
    elif "directory" in result and "results" in result:
        console.print(Panel(
            f"📁 **Directory**: {result['directory']}\n"
            f"📊 **Analysis**: {result['analysis_type']}\n"
            f"📄 **Files Found**: {result['total_files_found']}\n"
            f"🔍 **Files Analyzed**: {result['files_analyzed']}\n"
            f"🔤 **Languages**: {', '.join(result['languages_detected'])}",
            title="Directory Analysis Summary",
            style="green"
        ))
        
        # Show individual file results
        for i, file_result in enumerate(result['results']):
            if i >= 5:  # Limit display to first 5 files
                console.print(f"... and {len(result['results']) - 5} more files", style="dim")
                break
                
            if "error" not in file_result:
                console.print(f"\n📄 {file_result['file_path']} ({file_result['language']})")
                if isinstance(file_result['result'], dict) and file_result['result'].get('content'):
                    # Truncate long responses
                    content = file_result['result']['content']
                    if len(content) > 200:
                        content = content[:200] + "..."
                    console.print(f"   {content}", style="dim")
                else:
                    content = str(file_result['result'])
                    if len(content) > 200:
                        content = content[:200] + "..."
                    console.print(f"   {content}", style="dim")

def save_results(result: dict, output_path: str):
    """Save results to file"""
    import json
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)


# Add new CLI command
@app.command("analyze-repo")
def analyze_comprehensive_repo(
    path: str = typer.Argument(..., help="Repository path or GitHub URL"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for results")
):
    """Comprehensive analysis of entire repository"""
    console.print(f"🔍 Starting comprehensive analysis of {path}")
    
    scanner = ComprehensiveCodebaseScanner()
    
    async def run_analysis():
        results = await scanner.scan_codebase(path)
        
        # Display summary
        console.print(f"📊 Analysis complete:")
        console.print(f"  - Total files: {results.total_files}")
        console.print(f"  - Languages: {list(results.languages_detected.keys())}")
        console.print(f"  - Overall score: {results.overall_scores.get('overall', 0)}/10")
        
        if output:
            # Save detailed results
            with open(output, 'w') as f:
                import json
                json.dump({
                    "total_files": results.total_files,
                    "languages": results.languages_detected,
                    "scores": results.overall_scores,
                    "file_count_by_language": results.languages_detected
                }, f, indent=2)
            console.print(f"💾 Results saved to {output}")
    
    import asyncio
    asyncio.run(run_analysis())


@app.command()
def info():
    """Show CodeQualityAgent information"""
    
    table = Table(title="CodeQualityAgent Info")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Project Root", str(settings.project_root))
    table.add_row("Primary Model", settings.primary_model)
    table.add_row("Complex Model", settings.complex_model)
    table.add_row("Debug Mode", str(settings.debug))
    table.add_row("Max File Size", f"{settings.max_file_size_mb} MB")
    
    # Supported languages
    languages = ", ".join(settings.project_root.parent.name for _ in range(1))  # Placeholder
    from config.settings import SUPPORTED_LANGUAGES
    languages = ", ".join(SUPPORTED_LANGUAGES.keys())
    table.add_row("Supported Languages", languages)
    
    console.print(table)

if __name__ == "__main__":
    app()
