"""
Comprehensive Multi-Language Codebase Scanner
Analyzes entire repositories with deep relationship understanding
"""
import os
import asyncio
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import logging
import git
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor
import hashlib
import ast
import json
import re
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class FileAnalysis:
    """Comprehensive file analysis result"""
    filepath: str
    language: str
    size_bytes: int
    lines_of_code: int
    security_issues: List[Dict]
    performance_issues: List[Dict]
    quality_issues: List[Dict]
    complexity_metrics: Dict
    dependencies: List[str]
    duplicates: List[Dict]
    test_coverage: Optional[float]
    documentation_score: float

@dataclass
class CodebaseAnalysis:
    """Complete codebase analysis result"""
    total_files: int
    languages_detected: Dict[str, int]
    file_analyses: Dict[str, FileAnalysis]
    cross_file_relationships: Dict[str, List[str]]
    duplicate_blocks: List[Dict]
    architecture_issues: List[Dict]
    testing_gaps: List[Dict]
    overall_scores: Dict[str, float]

class ComprehensiveCodebaseScanner:
    """Multi-language codebase analyzer with deep relationship understanding"""
    
    SUPPORTED_LANGUAGES = {
        'python': {
            'extensions': ['.py', '.pyx', '.pyi'],
            'patterns': ['def ', 'class ', 'import ', 'from '],
            'complexity_keywords': ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'with']
        },
        'javascript': {
            'extensions': ['.js', '.jsx', '.ts', '.tsx', '.mjs'],
            'patterns': ['function ', 'const ', 'let ', 'var ', 'class ', 'import ', 'export'],
            'complexity_keywords': ['if', 'else', 'for', 'while', 'switch', 'case', 'try', 'catch']
        },
        'java': {
            'extensions': ['.java'],
            'patterns': ['public class', 'private', 'public', 'static', 'import'],
            'complexity_keywords': ['if', 'else', 'for', 'while', 'switch', 'case', 'try', 'catch']
        },
        'csharp': {
            'extensions': ['.cs'],
            'patterns': ['using ', 'namespace', 'public class', 'private', 'public'],
            'complexity_keywords': ['if', 'else', 'for', 'while', 'switch', 'case', 'try', 'catch']
        },
        'cpp': {
            'extensions': ['.cpp', '.cc', '.cxx', '.c', '.h', '.hpp'],
            'patterns': ['#include', 'class ', 'struct ', 'namespace'],
            'complexity_keywords': ['if', 'else', 'for', 'while', 'switch', 'case', 'try', 'catch']
        },
        'go': {
            'extensions': ['.go'],
            'patterns': ['package ', 'import ', 'func ', 'type ', 'var '],
            'complexity_keywords': ['if', 'else', 'for', 'switch', 'case', 'select']
        },
        'rust': {
            'extensions': ['.rs'],
            'patterns': ['fn ', 'struct ', 'impl ', 'use ', 'mod '],
            'complexity_keywords': ['if', 'else', 'for', 'while', 'loop', 'match']
        },
        'php': {
            'extensions': ['.php'],
            'patterns': ['<?php', 'function ', 'class ', '$'],
            'complexity_keywords': ['if', 'else', 'for', 'while', 'switch', 'case', 'try', 'catch']
        },
        'ruby': {
            'extensions': ['.rb'],
            'patterns': ['def ', 'class ', 'module ', 'require'],
            'complexity_keywords': ['if', 'elsif', 'else', 'for', 'while', 'case', 'when']
        },
        'swift': {
            'extensions': ['.swift'],
            'patterns': ['func ', 'class ', 'struct ', 'import'],
            'complexity_keywords': ['if', 'else', 'for', 'while', 'switch', 'case', 'do', 'catch']
        }
    }
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.file_hashes = {}
        self.duplicate_detector = DuplicateCodeDetector()
        self.relationship_analyzer = CrossFileAnalyzer()
        
    async def scan_codebase(self, path: str, options: Dict = None) -> CodebaseAnalysis:
        """Scan entire codebase comprehensively"""
        options = options or {}
        
        try:
            logger.info(f"🔍 Starting comprehensive scan of {path}")
            
            # Handle GitHub URLs
            if path.startswith('https://github.com/'):
                path = await self._clone_github_repo(path)
                
            # Collect all code files
            all_files = self._collect_all_code_files(path)
            logger.info(f"📁 Found {len(all_files)} code files across {len(self._detect_languages(all_files))} languages")
            
            # Analyze files in parallel
            file_analyses = await self._analyze_files_parallel(all_files)
            
            # Perform cross-file analysis
            relationships = await self._analyze_cross_file_relationships(file_analyses)
            
            # Detect duplicates across entire codebase
            duplicates = await self._detect_codebase_duplicates(file_analyses)
            
            # Analyze architecture and testing
            architecture_issues = await self._analyze_architecture(file_analyses, relationships)
            testing_gaps = await self._analyze_testing_coverage(file_analyses)
            
            # Calculate overall scores
            overall_scores = self._calculate_overall_scores(file_analyses)
            
            return CodebaseAnalysis(
                total_files=len(all_files),
                languages_detected=self._count_languages(file_analyses),
                file_analyses=file_analyses,
                cross_file_relationships=relationships,
                duplicate_blocks=duplicates,
                architecture_issues=architecture_issues,
                testing_gaps=testing_gaps,
                overall_scores=overall_scores
            )
            
        except Exception as e:
            logger.error(f"❌ Codebase scan failed: {e}")
            raise
    
    def _collect_all_code_files(self, root_path: str) -> List[str]:
        """Recursively collect all code files"""
        code_files = []
        root = Path(root_path)
        
        # Get all supported extensions
        all_extensions = set()
        for lang_config in self.SUPPORTED_LANGUAGES.values():
            all_extensions.update(lang_config['extensions'])
        
        # Patterns to exclude
        exclude_patterns = {
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            'build', 'dist', '.gradle', 'target', 'bin', 'obj',
            '.vs', '.vscode', '.idea', '*.min.js', '*.bundle.js'
        }
        
        # Walk through directory tree
        for file_path in root.rglob('*'):
            if file_path.is_file():
                # Check if it's a code file
                if file_path.suffix.lower() in all_extensions:
                    # Skip excluded directories
                    if not any(exclude in str(file_path) for exclude in exclude_patterns):
                        code_files.append(str(file_path))
        
        return sorted(code_files)
    
    async def _clone_github_repo(self, github_url: str) -> str:
        """Clone GitHub repository to temporary directory"""
        temp_dir = tempfile.mkdtemp()
        try:
            logger.info(f"📥 Cloning {github_url}")
            git.Repo.clone_from(github_url, temp_dir, depth=1)
            return temp_dir
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise Exception(f"Failed to clone repository: {e}")
    
    async def _analyze_files_parallel(self, file_paths: List[str]) -> Dict[str, FileAnalysis]:
        """Analyze all files in parallel"""
        tasks = []
        for file_path in file_paths:
            task = asyncio.create_task(self._analyze_single_file(file_path))
            tasks.append(task)
        
        # Process in batches to avoid overwhelming the system
        batch_size = 20
        results = {}
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            for j, result in enumerate(batch_results):
                if isinstance(result, FileAnalysis):
                    results[file_paths[i + j]] = result
                else:
                    logger.warning(f"Failed to analyze {file_paths[i + j]}: {result}")
        
        return results
    
    async def _analyze_single_file(self, file_path: str) -> FileAnalysis:
        """Comprehensive analysis of a single file"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Detect language
            language = self._detect_file_language(file_path, content)
            
            # Basic metrics
            size_bytes = len(content.encode('utf-8'))
            lines_of_code = len([line for line in content.split('\n') if line.strip()])
            
            # Security analysis
            security_issues = await self._analyze_security(content, language, file_path)
            
            # Performance analysis
            performance_issues = await self._analyze_performance(content, language, file_path)
            
            # Code quality analysis
            quality_issues = await self._analyze_code_quality(content, language, file_path)
            
            # Complexity metrics
            complexity_metrics = self._calculate_complexity(content, language)
            
            # Dependencies
            dependencies = self._extract_dependencies(content, language)
            
            # Documentation score
            documentation_score = self._calculate_documentation_score(content, language)
            
            return FileAnalysis(
                filepath=file_path,
                language=language,
                size_bytes=size_bytes,
                lines_of_code=lines_of_code,
                security_issues=security_issues,
                performance_issues=performance_issues,
                quality_issues=quality_issues,
                complexity_metrics=complexity_metrics,
                dependencies=dependencies,
                duplicates=[],  # Will be filled by duplicate detector
                test_coverage=None,  # Will be calculated separately
                documentation_score=documentation_score
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            raise
    
    def _detect_file_language(self, file_path: str, content: str) -> str:
        """Detect programming language from file extension and content"""
        file_ext = Path(file_path).suffix.lower()
        
        # First try by extension
        for lang, config in self.SUPPORTED_LANGUAGES.items():
            if file_ext in config['extensions']:
                return lang
        
        # If extension doesn't match, analyze content
        pattern_scores = {}
        for lang, config in self.SUPPORTED_LANGUAGES.items():
            score = 0
            for pattern in config['patterns']:
                score += content.count(pattern)
            pattern_scores[lang] = score
        
        # Return language with highest pattern score
        if pattern_scores:
            return max(pattern_scores, key=pattern_scores.get)
        
        return 'unknown'
    
    async def _analyze_security(self, content: str, language: str, file_path: str) -> List[Dict]:
        """Comprehensive security analysis"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Hardcoded secrets
            if self._detect_hardcoded_secrets(line_stripped):
                issues.append({
                    'type': 'security',
                    'severity': 'critical',
                    'category': 'Hardcoded Secrets',
                    'line': i,
                    'code': line_stripped,
                    'message': 'Hardcoded credentials detected',
                    'cwe': 'CWE-798'
                })
            
            # SQL Injection
            if self._detect_sql_injection(line_stripped, language):
                issues.append({
                    'type': 'security',
                    'severity': 'critical',
                    'category': 'SQL Injection',
                    'line': i,
                    'code': line_stripped,
                    'message': 'Potential SQL injection vulnerability',
                    'cwe': 'CWE-89'
                })
            
            # XSS vulnerabilities
            if self._detect_xss_vulnerability(line_stripped, language):
                issues.append({
                    'type': 'security',
                    'severity': 'high',
                    'category': 'Cross-Site Scripting',
                    'line': i,
                    'code': line_stripped,
                    'message': 'Potential XSS vulnerability',
                    'cwe': 'CWE-79'
                })
            
            # Path traversal
            if self._detect_path_traversal(line_stripped, language):
                issues.append({
                    'type': 'security',
                    'severity': 'high',
                    'category': 'Path Traversal',
                    'line': i,
                    'code': line_stripped,
                    'message': 'Potential path traversal vulnerability',
                    'cwe': 'CWE-22'
                })
            
            # Insecure random number generation
            if self._detect_weak_random(line_stripped, language):
                issues.append({
                    'type': 'security',
                    'severity': 'medium',
                    'category': 'Weak Cryptography',
                    'line': i,
                    'code': line_stripped,
                    'message': 'Weak random number generation',
                    'cwe': 'CWE-338'
                })
        
        return issues
    
    async def _analyze_performance(self, content: str, language: str, file_path: str) -> List[Dict]:
        """Comprehensive performance analysis"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Inefficient loops
            if self._detect_inefficient_loops(line_stripped, language):
                issues.append({
                    'type': 'performance',
                    'severity': 'high',
                    'category': 'Algorithm Efficiency',
                    'line': i,
                    'code': line_stripped,
                    'message': 'Inefficient loop pattern detected'
                })
            
            # Memory leaks
            if self._detect_memory_issues(line_stripped, language):
                issues.append({
                    'type': 'performance',
                    'severity': 'high',
                    'category': 'Memory Management',
                    'line': i,
                    'code': line_stripped,
                    'message': 'Potential memory leak or excessive allocation'
                })
            
            # Blocking operations
            if self._detect_blocking_operations(line_stripped, language):
                issues.append({
                    'type': 'performance',
                    'severity': 'medium',
                    'category': 'Concurrency',
                    'line': i,
                    'code': line_stripped,
                    'message': 'Blocking operation in async context'
                })
            
            # Database query issues
            if self._detect_db_performance_issues(line_stripped, language):
                issues.append({
                    'type': 'performance',
                    'severity': 'medium',
                    'category': 'Database',
                    'line': i,
                    'code': line_stripped,
                    'message': 'Inefficient database operation'
                })
        
        return issues
    
    async def _analyze_code_quality(self, content: str, language: str, file_path: str) -> List[Dict]:
        """Comprehensive code quality analysis"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Magic numbers
            if self._detect_magic_numbers(line_stripped, language):
                issues.append({
                    'type': 'quality',
                    'severity': 'low',
                    'category': 'Maintainability',
                    'line': i,
                    'code': line_stripped,
                    'message': 'Magic number should be a named constant'
                })
            
            # Long parameter lists
            if self._detect_long_parameter_lists(line_stripped, language):
                issues.append({
                    'type': 'quality',
                    'severity': 'medium',
                    'category': 'Code Smell',
                    'line': i,
                    'code': line_stripped,
                    'message': 'Function has too many parameters'
                })
            
            # Dead code
            if self._detect_dead_code(line_stripped, language):
                issues.append({
                    'type': 'quality',
                    'severity': 'low',
                    'category': 'Dead Code',
                    'line': i,
                    'code': line_stripped,
                    'message': 'Unreachable or dead code detected'
                })
            
            # Missing error handling
            if self._detect_missing_error_handling(line_stripped, language):
                issues.append({
                    'type': 'quality',
                    'severity': 'medium',
                    'category': 'Error Handling',
                    'line': i,
                    'code': line_stripped,
                    'message': 'Missing or inadequate error handling'
                })
        
        return issues
    
    # Helper methods for detection
    def _detect_hardcoded_secrets(self, line: str) -> bool:
        """Detect hardcoded secrets"""
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'key\s*=\s*["\'][A-Za-z0-9+/]{20,}["\']'
        ]
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in secret_patterns)
    
    def _detect_sql_injection(self, line: str, language: str) -> bool:
        """Detect SQL injection vulnerabilities"""
        if language in ['python', 'java', 'csharp', 'php']:
            sql_patterns = [
                r'(SELECT|INSERT|UPDATE|DELETE).*\+.*["\']',
                r'query.*=.*["\'].*\+',
                r'execute\(.*\+.*\)',
                r'format.*SELECT.*%s'
            ]
            return any(re.search(pattern, line, re.IGNORECASE) for pattern in sql_patterns)
        return False
    
    def _detect_xss_vulnerability(self, line: str, language: str) -> bool:
        """Detect XSS vulnerabilities"""
        if language in ['javascript', 'php']:
            xss_patterns = [
                r'innerHTML\s*=.*\+',
                r'document\.write\(.*\+',
                r'echo.*\$_GET',
                r'echo.*\$_POST'
            ]
            return any(re.search(pattern, line, re.IGNORECASE) for pattern in xss_patterns)
        return False
    
    def _detect_path_traversal(self, line: str, language: str) -> bool:
        """Detect path traversal vulnerabilities"""
        path_patterns = [
            r'open\(.*\+.*\)',
            r'readFile\(.*\+.*\)',
            r'include.*\$_GET',
            r'require.*\$_POST'
        ]
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in path_patterns)
    
    def _detect_weak_random(self, line: str, language: str) -> bool:
        """Detect weak random number generation"""
        weak_random_patterns = {
            'python': [r'random\.random\(', r'random\.randint\('],
            'java': [r'Math\.random\(', r'Random\(\)\.next'],
            'javascript': [r'Math\.random\('],
        }
        if language in weak_random_patterns:
            return any(re.search(pattern, line) for pattern in weak_random_patterns[language])
        return False
    
    def _detect_inefficient_loops(self, line: str, language: str) -> bool:
        """Detect inefficient loop patterns"""
        inefficient_patterns = {
            'python': [r'for.*range\(len\(.*\)\):', r'while.*len\(.*\) >'],
            'java': [r'for.*\.size\(\).*\+\+', r'\.get\(.*\).*for'],
            'javascript': [r'for.*\.length.*\+\+', r'while.*\.length >']
        }
        if language in inefficient_patterns:
            return any(re.search(pattern, line) for pattern in inefficient_patterns[language])
        return False
    
    def _detect_memory_issues(self, line: str, language: str) -> bool:
        """Detect potential memory issues"""
        memory_patterns = [
            r'range\(10000',
            r'new.*\[1000000',
            r'malloc\(.*\*.*\*',
            r'ArrayList.*100000'
        ]
        return any(re.search(pattern, line) for pattern in memory_patterns)
    
    def _detect_blocking_operations(self, line: str, language: str) -> bool:
        """Detect blocking operations"""
        blocking_patterns = {
            'python': [r'time\.sleep\(', r'requests\.get\(', r'\.read\(\)'],
            'javascript': [r'fs\.readFileSync', r'XMLHttpRequest\(\)'],
            'java': [r'Thread\.sleep\(', r'\.read\(\)']
        }
        if language in blocking_patterns:
            return any(re.search(pattern, line) for pattern in blocking_patterns[language])
        return False
    
    def _detect_db_performance_issues(self, line: str, language: str) -> bool:
        """Detect database performance issues"""
        db_patterns = [
            r'SELECT \*',
            r'for.*execute\(',
            r'while.*query\(',
            r'N\+1.*query'
        ]
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in db_patterns)
    
    def _detect_magic_numbers(self, line: str, language: str) -> bool:
        """Detect magic numbers"""
        if re.search(r'[^a-zA-Z_]\d{2,}[^a-zA-Z_]', line):
            # Exclude common exceptions
            exceptions = ['100', '200', '404', '500', '1000', '0', '1', '2']
            for exc in exceptions:
                if exc in line:
                    return False
            return True
        return False
    
    def _detect_long_parameter_lists(self, line: str, language: str) -> bool:
        """Detect functions with too many parameters"""
        func_patterns = {
            'python': r'def\s+\w+\(([^)]*)\):',
            'java': r'public.*\w+\(([^)]*)\)',
            'javascript': r'function\s+\w+\(([^)]*)\)'
        }
        if language in func_patterns:
            match = re.search(func_patterns[language], line)
            if match:
                params = match.group(1).split(',')
                return len([p for p in params if p.strip()]) > 5
        return False
    
    def _detect_dead_code(self, line: str, language: str) -> bool:
        """Detect dead/unreachable code"""
        dead_patterns = [
            r'if\s+(false|False|0):',
            r'if\s*\(\s*(false|0)\s*\)',
            r'while\s+(false|False|0):',
            r'return.*;\s*\w+'  # Code after return
        ]
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in dead_patterns)
    
    def _detect_missing_error_handling(self, line: str, language: str) -> bool:
        """Detect missing error handling"""
        risky_patterns = {
            'python': [r'open\(.*\)', r'json\.loads\(', r'int\(.*\)'],
            'java': [r'Integer\.parseInt\(', r'new FileReader\('],
            'javascript': [r'JSON\.parse\(', r'parseInt\(']
        }
        if language in risky_patterns:
            return any(re.search(pattern, line) for pattern in risky_patterns[language])
        return False
    
    def _calculate_complexity(self, content: str, language: str) -> Dict:
        """Calculate complexity metrics"""
        if language not in self.SUPPORTED_LANGUAGES:
            return {'cyclomatic_complexity': 0, 'cognitive_complexity': 0}
        
        complexity_keywords = self.SUPPORTED_LANGUAGES[language]['complexity_keywords']
        
        # Cyclomatic complexity (simplified)
        cyclomatic = 1  # Base complexity
        for keyword in complexity_keywords:
            cyclomatic += content.count(keyword + ' ')
        
        # Cognitive complexity (considers nesting)
        cognitive = self._calculate_cognitive_complexity(content, language)
        
        return {
            'cyclomatic_complexity': cyclomatic,
            'cognitive_complexity': cognitive,
            'nesting_depth': self._calculate_nesting_depth(content, language)
        }
    
    def _calculate_cognitive_complexity(self, content: str, language: str) -> int:
        """Calculate cognitive complexity"""
        # Simplified cognitive complexity calculation
        nesting_level = 0
        cognitive_complexity = 0
        
        lines = content.split('\n')
        for line in lines:
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            # Update nesting level based on indentation
            if language == 'python':
                current_nesting = indent // 4
            else:
                current_nesting = stripped.count('{') - stripped.count('}')
            
            # Add complexity for control structures
            if any(keyword in stripped for keyword in ['if', 'for', 'while', 'switch']):
                cognitive_complexity += 1 + current_nesting
        
        return cognitive_complexity
    
    def _calculate_nesting_depth(self, content: str, language: str) -> int:
        """Calculate maximum nesting depth"""
        max_depth = 0
        current_depth = 0
        
        lines = content.split('\n')
        for line in lines:
            stripped = line.strip()
            
            if language == 'python':
                # Python uses indentation
                indent = len(line) - len(line.lstrip())
                current_depth = indent // 4
            else:
                # Other languages use braces
                current_depth += stripped.count('{') - stripped.count('}')
            
            max_depth = max(max_depth, current_depth)
        
        return max_depth
    
    def _extract_dependencies(self, content: str, language: str) -> List[str]:
        """Extract file dependencies"""
        dependencies = []
        
        dependency_patterns = {
            'python': [r'import\s+(\w+)', r'from\s+(\w+)\s+import'],
            'javascript': [r'import.*from\s+["\'](.+)["\']', r'require\(["\'](.+)["\']\)'],
            'java': [r'import\s+([\w.]+);'],
            'csharp': [r'using\s+([\w.]+);'],
            'go': [r'import\s+"(.+)"'],
            'rust': [r'use\s+([\w:]+);']
        }
        
        if language in dependency_patterns:
            for pattern in dependency_patterns[language]:
                matches = re.findall(pattern, content, re.MULTILINE)
                dependencies.extend(matches)
        
        return list(set(dependencies))  # Remove duplicates
    
    def _calculate_documentation_score(self, content: str, language: str) -> float:
        """Calculate documentation coverage score"""
        lines = content.split('\n')
        total_lines = len([line for line in lines if line.strip()])
        
        if total_lines == 0:
            return 0.0
        
        # Count documentation lines
        doc_lines = 0
        comment_patterns = {
            'python': [r'^\s*#', r'^\s*"""', r'^\s*\'\'\''],
            'javascript': [r'^\s*//', r'^\s*/\*', r'^\s*\*'],
            'java': [r'^\s*//', r'^\s*/\*', r'^\s*\*'],
            'csharp': [r'^\s*//', r'^\s*/\*', r'^\s*\*'],
            'cpp': [r'^\s*//', r'^\s*/\*', r'^\s*\*'],
            'go': [r'^\s*//'],
            'rust': [r'^\s*//', r'^\s*/\*'],
            'php': [r'^\s*//', r'^\s*/\*', r'^\s*\*'],
            'ruby': [r'^\s*#'],
            'swift': [r'^\s*//', r'^\s*/\*']
        }
        
        if language in comment_patterns:
            for line in lines:
                if any(re.match(pattern, line) for pattern in comment_patterns[language]):
                    doc_lines += 1
        
        return min(1.0, doc_lines / total_lines)
    
    async def _analyze_cross_file_relationships(self, file_analyses: Dict[str, FileAnalysis]) -> Dict[str, List[str]]:
        """Analyze relationships between files"""
        relationships = defaultdict(list)
        
        for file_path, analysis in file_analyses.items():
            # Map dependencies to actual files in the codebase
            for dep in analysis.dependencies:
                for other_file, other_analysis in file_analyses.items():
                    if other_file != file_path:
                        # Check if dependency matches file name or module
                        if self._dependency_matches_file(dep, other_file, other_analysis.language):
                            relationships[file_path].append(other_file)
        
        return dict(relationships)
    
    def _dependency_matches_file(self, dependency: str, file_path: str, language: str) -> bool:
        """Check if a dependency matches a file"""
        file_name = Path(file_path).stem
        
        # Simple matching logic - can be enhanced
        if dependency.lower() in file_name.lower():
            return True
        
        if file_name.lower() in dependency.lower():
            return True
        
        return False
    
    async def _detect_codebase_duplicates(self, file_analyses: Dict[str, FileAnalysis]) -> List[Dict]:
        """Detect duplicate code blocks across the entire codebase"""
        duplicates = []
        
        # Simple duplicate detection based on content hashing
        file_contents = {}
        for file_path, analysis in file_analyses.items():
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    file_contents[file_path] = content
            except:
                continue
        
        # Look for duplicate blocks
        for file1, content1 in file_contents.items():
            for file2, content2 in file_contents.items():
                if file1 >= file2:  # Avoid duplicate comparisons
                    continue
                
                duplicate_blocks = self._find_duplicate_blocks(content1, content2, file1, file2)
                duplicates.extend(duplicate_blocks)
        
        return duplicates
    
    def _find_duplicate_blocks(self, content1: str, content2: str, file1: str, file2: str) -> List[Dict]:
        """Find duplicate code blocks between two files"""
        duplicates = []
        lines1 = content1.split('\n')
        lines2 = content2.split('\n')
        
        min_block_size = 5  # Minimum lines for a duplicate block
        
        for i in range(len(lines1) - min_block_size):
            for j in range(len(lines2) - min_block_size):
                # Check for matching blocks
                block_size = 0
                while (i + block_size < len(lines1) and 
                       j + block_size < len(lines2) and
                       lines1[i + block_size].strip() == lines2[j + block_size].strip() and
                       lines1[i + block_size].strip()):  # Skip empty lines
                    block_size += 1
                
                if block_size >= min_block_size:
                    duplicates.append({
                        'file1': file1,
                        'file2': file2,
                        'lines1': f"{i+1}-{i+block_size}",
                        'lines2': f"{j+1}-{j+block_size}",
                        'duplicate_lines': block_size,
                        'similarity': 1.0  # Exact match
                    })
        
        return duplicates
    
    async def _analyze_architecture(self, file_analyses: Dict[str, FileAnalysis], relationships: Dict[str, List[str]]) -> List[Dict]:
        """Analyze architecture issues"""
        issues = []
        
        # Circular dependencies
        circular_deps = self._detect_circular_dependencies(relationships)
        for cycle in circular_deps:
            issues.append({
                'type': 'architecture',
                'severity': 'high',
                'category': 'Circular Dependency',
                'message': f'Circular dependency detected: {" -> ".join(cycle)}',
                'files': cycle
            })
        
        # God classes/files (too many dependencies)
        for file_path, deps in relationships.items():
            if len(deps) > 10:  # Threshold for too many dependencies
                issues.append({
                    'type': 'architecture',
                    'severity': 'medium',
                    'category': 'God Class',
                    'message': f'File has too many dependencies: {len(deps)}',
                    'file': file_path,
                    'dependency_count': len(deps)
                })
        
        return issues
    
    def _detect_circular_dependencies(self, relationships: Dict[str, List[str]]) -> List[List[str]]:
        """Detect circular dependencies using DFS"""
        def dfs(node, path, visited):
            if node in path:
                # Found a cycle
                cycle_start = path.index(node)
                return [path[cycle_start:] + [node]]
            
            if node in visited:
                return []
            
            visited.add(node)
            path.append(node)
            
            cycles = []
            for neighbor in relationships.get(node, []):
                cycles.extend(dfs(neighbor, path, visited))
            
            path.pop()
            return cycles
        
        all_cycles = []
        visited = set()
        
        for node in relationships:
            if node not in visited:
                cycles = dfs(node, [], visited)
                all_cycles.extend(cycles)
        
        return all_cycles
    
    async def _analyze_testing_coverage(self, file_analyses: Dict[str, FileAnalysis]) -> List[Dict]:
        """Analyze testing gaps"""
        issues = []
        
        # Find test files
        test_files = []
        source_files = []
        
        for file_path in file_analyses.keys():
            if any(test_indicator in file_path.lower() for test_indicator in ['test', 'spec', '__test__']):
                test_files.append(file_path)
            else:
                source_files.append(file_path)
        
        # Calculate test coverage ratio
        if source_files:
            test_ratio = len(test_files) / len(source_files)
            if test_ratio < 0.3:  # Less than 30% test coverage
                issues.append({
                    'type': 'testing',
                    'severity': 'high',
                    'category': 'Low Test Coverage',
                    'message': f'Low test coverage: {test_ratio:.1%} (target: >30%)',
                    'test_files': len(test_files),
                    'source_files': len(source_files)
                })
        
        # Look for files without corresponding tests
        for source_file in source_files:
            source_name = Path(source_file).stem
            has_test = any(source_name.lower() in test_file.lower() for test_file in test_files)
            
            if not has_test:
                issues.append({
                    'type': 'testing',
                    'severity': 'medium',
                    'category': 'Missing Tests',
                    'message': f'No test file found for {source_name}',
                    'file': source_file
                })
        
        return issues
    
    def _calculate_overall_scores(self, file_analyses: Dict[str, FileAnalysis]) -> Dict[str, float]:
        """Calculate overall quality scores"""
        if not file_analyses:
            return {}
        
        total_files = len(file_analyses)
        
        # Count issues by category
        security_issues = sum(len(analysis.security_issues) for analysis in file_analyses.values())
        performance_issues = sum(len(analysis.performance_issues) for analysis in file_analyses.values())
        quality_issues = sum(len(analysis.quality_issues) for analysis in file_analyses.values())
        
        # Calculate scores (10 - issues per file, minimum 1)
        security_score = max(1, 10 - (security_issues / total_files * 2))
        performance_score = max(1, 10 - (performance_issues / total_files * 1.5))
        quality_score = max(1, 10 - (quality_issues / total_files))
        
        # Documentation score (average)
        doc_score = sum(analysis.documentation_score for analysis in file_analyses.values()) / total_files * 10
        
        # Complexity score (inverse of average complexity)
        avg_complexity = sum(analysis.complexity_metrics.get('cyclomatic_complexity', 0) for analysis in file_analyses.values()) / total_files
        complexity_score = max(1, 10 - (avg_complexity / 5))
        
        return {
            'security': round(security_score, 1),
            'performance': round(performance_score, 1),
            'maintainability': round(quality_score, 1),
            'documentation': round(doc_score, 1),
            'complexity': round(complexity_score, 1),
            'overall': round((security_score + performance_score + quality_score + doc_score + complexity_score) / 5, 1)
        }
    
    def _count_languages(self, file_analyses: Dict[str, FileAnalysis]) -> Dict[str, int]:
        """Count files by language"""
        language_count = defaultdict(int)
        for analysis in file_analyses.values():
            language_count[analysis.language] += 1
        return dict(language_count)
    
    def _detect_languages(self, file_paths: List[str]) -> Set[str]:
        """Detect all languages in the codebase"""
        languages = set()
        for file_path in file_paths:
            ext = Path(file_path).suffix.lower()
            for lang, config in self.SUPPORTED_LANGUAGES.items():
                if ext in config['extensions']:
                    languages.add(lang)
                    break
        return languages

# Additional helper classes
class DuplicateCodeDetector:
    """Specialized duplicate code detection"""
    
    def __init__(self):
        self.min_block_size = 5
        self.similarity_threshold = 0.8

class CrossFileAnalyzer:
    """Analyze relationships between files"""
    
    def __init__(self):
        self.dependency_graph = {}
