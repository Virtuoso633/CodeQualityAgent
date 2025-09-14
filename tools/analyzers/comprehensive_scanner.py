"""
Comprehensive Codebase Scanner - FINAL BUGFIXED VERSION
"""
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
import git
import tempfile
import shutil
import ast
from dataclasses import dataclass
from collections import defaultdict
import re
import os

from config.settings import settings, SUPPORTED_LANGUAGES
from agents.specialized.security_agent import get_security_agent
from agents.specialized.performance_agent import get_performance_agent
from agents.specialized.performance_agent import get_performance_agent
from agents.specialized.architecture_agent import get_architecture_agent

logger = logging.getLogger(__name__)

@dataclass
class FileAnalysis:
    filepath: str; language: str; size_bytes: int; lines_of_code: int
    security_issues: List[Dict]; performance_issues: List[Dict]; quality_issues: List[Dict]
    complexity_metrics: Dict; dependencies: List[str]; documentation_score: float

@dataclass
class CodebaseAnalysis:
    total_files: int
    languages_detected: Dict[str, int]
    file_analyses: Dict[str, FileAnalysis]
    cross_file_relationships: Dict[str, List[str]]
    duplicate_blocks: List[Dict]
    architecture_summary: str  # This is the line that was missing
    testing_gaps: List[Dict]
    overall_scores: Dict[str, float]
    
class ComprehensiveCodebaseScanner:
    SUPPORTED_LANGUAGES = SUPPORTED_LANGUAGES
    
    def __init__(self):
        self.security_agent = get_security_agent()
        self.performance_agent = get_performance_agent()
        self.architecture_agent = get_architecture_agent()

    async def scan_codebase(self, path: str) -> CodebaseAnalysis:
        cloned_path = path
        is_temp_clone = False
        try:
            if path.startswith('https://github.com/'):
                cloned_path = await self._clone_github_repo(path)
                is_temp_clone = True
            
            all_files = self._collect_all_code_files(cloned_path)
            if not all_files: raise ValueError("No supported code files found.")
            logger.info(f"📁 Found {len(all_files)} files. Delegating to agents...")

            # Run file-level analysis
            tasks = [self._analyze_single_file(f, Path(cloned_path)) for f in all_files]
            results = await asyncio.gather(*tasks)
            file_analyses = {res.filepath: res for res in results if res}
            
            # Run codebase-level analysis
            relative_file_paths = [str(p.relative_to(cloned_path)) for p in all_files]
            arch_task = self.architecture_agent.analyze_codebase_structure(relative_file_paths)
            architecture_summary = await arch_task # GET ARCHITECTURE SUMMARY

            relationships = self._analyze_cross_file_relationships(file_analyses)
            testing_gaps = self._analyze_testing_coverage(file_analyses)
            overall_scores = self._calculate_overall_scores(file_analyses, [], testing_gaps)

            return CodebaseAnalysis(
                total_files=len(all_files), languages_detected=self._count_languages(file_analyses),
                file_analyses=file_analyses, cross_file_relationships=relationships,
                duplicate_blocks=[], architecture_summary=architecture_summary, # ADD THIS
                testing_gaps=testing_gaps, overall_scores=overall_scores
            )
        finally:
            if is_temp_clone and os.path.isdir(cloned_path):
                shutil.rmtree(cloned_path, ignore_errors=True)
    
    async def _clone_github_repo(self, github_url: str) -> str:
        temp_dir = tempfile.mkdtemp()
        try:
            clone_url = github_url.replace("https://", f"https://{settings.github_token}@") if settings.github_token else github_url
            await asyncio.to_thread(git.Repo.clone_from, clone_url, temp_dir, depth=1)
            return temp_dir
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise Exception(f"Failed to clone repository. Is it private? Set GITHUB_TOKEN. Error: {e}")

    def _collect_all_code_files(self, root_path: str) -> List[Path]:
        all_exts = {e for lang in self.SUPPORTED_LANGUAGES.values() for e in lang['extensions']}
        exclude = {'.git', '__pycache__', 'node_modules', 'build', 'dist'}
        return [p for p in Path(root_path).rglob('*') if p.is_file() and p.suffix.lower() in all_exts and not any(d in p.parts for d in exclude)]

    async def _analyze_single_file(self, file_path: Path, root_path: Path) -> Optional[FileAnalysis]:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            language = self._detect_file_language(file_path)
            if not language: return None

            sec_task = self.security_agent.analyze_code(content, language)
            perf_task = self.performance_agent.analyze_code(content, language)
            sec_res, perf_res = await asyncio.gather(sec_task, perf_task)
            
            qual_iss, comp_met = self._analyze_python_with_ast(content) if language == 'python' else ([], {})

            return FileAnalysis(
                filepath=str(file_path.relative_to(root_path)), language=language,
                size_bytes=len(content.encode('utf-8')), lines_of_code=len(content.splitlines()),
                security_issues=sec_res.get("issues", []),
                performance_issues=perf_res.get("issues", []),
                quality_issues=qual_iss, complexity_metrics=comp_met,
                dependencies=self._extract_dependencies(content, language),
                documentation_score=self._calculate_documentation_score(content)
            )
        except Exception as e:
            logger.error(f"Error analyzing {file_path.name}: {e}")
            return None

    def _analyze_python_with_ast(self, content: str) -> tuple[List[Dict], Dict]:
        # --- THIS IS THE NEW, MORE POWERFUL AST ANALYSIS ---
        issues, complexity_total = [], 0
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for long parameter lists
                    if len(node.args.args) > 5:
                        issues.append({'line': node.lineno, 'severity': 'Medium', 'type': 'Long Parameter List', 'explanation': f"Function '{node.name}' has {len(node.args.args)} parameters, which can make it hard to use and test."})
                    
                    # Calculate and accumulate cyclomatic complexity
                    complexity = self._get_cyclomatic_complexity(node)
                    if complexity > 10:
                        issues.append({'line': node.lineno, 'severity': 'High', 'type': 'High Cyclomatic Complexity', 'explanation': f"Function '{node.name}' has a complexity of {complexity}, making it difficult to understand and maintain."})
                    complexity_total += complexity

                elif isinstance(node, ast.ExceptHandler):
                    # Check for broad 'except Exception'
                    if isinstance(node.type, ast.Name) and node.type.id == 'Exception':
                        issues.append({'line': node.lineno, 'severity': 'Medium', 'type': 'Broad Exception Clause', 'explanation': "Catching a broad 'Exception' can hide unexpected errors. Catch more specific exceptions."})
                    # Check for empty 'except:' blocks
                    if not node.body or (len(node.body) == 1 and isinstance(node.body, ast.Pass)):
                        issues.append({'line': node.lineno, 'severity': 'High', 'type': 'Empty Except Block', 'explanation': "An empty 'except' block swallows errors silently, making debugging extremely difficult."})

        except SyntaxError as e:
            issues.append({'line': e.lineno, 'severity': 'Critical', 'type': 'Syntax Error', 'explanation': f"Code has a syntax error: {e}"})
        
        return issues, {'cyclomatic_complexity': complexity_total}
    
    def _get_cyclomatic_complexity(self, node):
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.And, ast.Or, ast.ExceptHandler, ast.withitem)):
                complexity += 1
        return complexity

    def _detect_file_language(self, fp: Path) -> Optional[str]:
        return next((lang for lang, c in self.SUPPORTED_LANGUAGES.items() if fp.suffix.lower() in c['extensions']), None)
    
    def _extract_dependencies(self, content: str, language: str) -> List[str]:
        if language != 'python': return []
        return [m for g in re.findall(r'^\s*import\s+([\w.]+)|^\s*from\s+([\w.]+)', content, re.M) for m in g if m]

    def _calculate_documentation_score(self, content: str) -> float:
        lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
        if not lines: return 0.0
        doc_lines = sum(1 for ln in lines if ln.startswith('#') or ln.startswith('//') or ln.startswith('"""'))
        return round(min(1.0, (doc_lines / len(lines)) * 2.5) * 10, 1)

    def _analyze_cross_file_relationships(self, file_analyses: Dict[str, FileAnalysis]) -> Dict[str, List[str]]:
        return {}

    def _analyze_architecture(self, relationships: Dict[str, List[str]]) -> List[Dict]:
        return []

    def _analyze_testing_coverage(self, file_analyses: Dict[str, FileAnalysis]) -> List[Dict]:
        src = [f for f in file_analyses if 'test' not in f.lower()]
        tst = [f for f in file_analyses if 'test' in f.lower()]
        ratio = len(tst) / len(src) if src else 1
        if ratio < 0.3:
            return [{'severity': 'High', 'category': 'Low Test Coverage', 'message': f"Only {len(tst)} test files for {len(src)} source files ({ratio:.1%})."}]
        return []

    def _count_languages(self, analyses: Dict[str, FileAnalysis]) -> Dict[str, int]:
        counts = defaultdict(int)
        for analysis in analyses.values(): counts[analysis.language] += 1
        return dict(counts)


    def _calculate_overall_scores(self, analyses: Dict, arch_issues, test_gaps) -> Dict[str, float]:
        if not analyses: return {}
        num_files = len(analyses)
        
        # --- THIS IS THE FIX: More balanced severity weights ---
        sec_sev = {"Critical": 2.5, "High": 1.5, "Medium": 0.5, "Low": 0.2}
        perf_sev = {"High": 2.0, "Medium": 1.0, "Low": 0.3}
        # --- END OF FIX ---

        sec_impact = sum(sec_sev.get(i['severity'], 0) for a in analyses.values() for i in a.security_issues)
        perf_impact = sum(perf_sev.get(i['severity'], 0) for a in analyses.values() for i in a.performance_issues)
        
        # The formula remains the same, but now uses the more balanced impact scores
        sec_score = max(0.0, 10.0 - (sec_impact / num_files))
        perf_score = max(0.0, 10.0 - (perf_impact / num_files))
        doc_score = sum(a.documentation_score for a in analyses.values()) / num_files if num_files > 0 else 0.0
        maint_score = max(0.0, 10.0 - (len(arch_issues) * 2) - (len(test_gaps) * 1))
        
        overall = (sec_score + perf_score + doc_score + maint_score) / 4
        
        return {k: round(v, 1) for k, v in {
            'overall': overall, 'security': sec_score, 'performance': perf_score,
            'maintainability': maint_score, 'documentation': doc_score, 'complexity': 8.0 # Complexity can be improved later
        }.items()}
        