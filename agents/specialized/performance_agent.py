"""
Specialized Performance Analysis Agent
"""
import asyncio
import ast
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from models.gemini.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)

class PerformanceAnalysisAgent:
    """Specialized agent for performance bottleneck analysis"""
    
    def __init__(self):
        """Initialize performance agent"""
        self.gemini_client = get_gemini_client()
        self.performance_patterns = {
            "python": {
                "inefficient_loops": [
                    r"for\s+\w+\s+in\s+range\s*\(\s*len\s*\(",  # for i in range(len(list))
                    r"while\s+.*len\s*\(",                        # while with len()
                    r"for\s+.*\.append\s*\(.*for\s+.*in"        # nested loops with append
                ],
                "memory_issues": [
                    r"\[\s*.*\s*for\s+.*\s+in\s+range\s*\(\s*\d{6,}\s*\)",  # Large list comprehensions
                    r"range\s*\(\s*\d{6,}\s*\)",                              # Large ranges
                    r".*\*.*\*.*\*.*\*"                                       # Multiple multiplications (potential factorial/exponential)
                ],
                "inefficient_operations": [
                    r"\.extend\s*\(\s*\[.*\]\s*\)",              # extend with list literal
                    r"\+\s*=\s*\[.*\]",                          # += with list (creates new list)
                    r".*\.sort\s*\(\s*\).*\.sort\s*\(\s*\)"     # Multiple sorts
                ],
                "string_concatenation": [
                    r"\w+\s*\+\s*=\s*.*str\s*\(",               # String concatenation in loop
                    r"['\"].*['\"].*\+.*['\"].*['\"]"            # Multiple string concatenations
                ]
            },
            "javascript": {
                "dom_performance": [
                    r"document\.getElementById.*in.*for",        # DOM queries in loops
                    r"getElementsBy.*in.*for",                   # DOM queries in loops
                    r"querySelector.*in.*for"                    # DOM queries in loops
                ],
                "inefficient_loops": [
                    r"for\s*\(\s*var\s+.*length\s*;",           # Recalculating length in loop
                    r"while\s*\(.*\.length\s*>"                 # Length check in while loop
                ],
                "memory_leaks": [
                    r"setInterval\s*\(",                         # Potential memory leaks
                    r"addEventListener.*without.*remove",        # Event listeners without removal
                    r"new\s+Array\s*\(\s*\d{6,}\s*\)"          # Large array creation
                ]
            }
        }
    
    async def analyze_performance_patterns(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code for performance anti-patterns"""
        try:
            findings = {
                "pattern_matches": {},
                "performance_score": 10,  # Start with perfect score
                "total_issues": 0,
                "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0}
            }
            
            if language not in self.performance_patterns:
                return findings
            
            # Check each performance pattern category
            for category, patterns in self.performance_patterns[language].items():
                matches = []
                
                for pattern in patterns:
                    found_matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
                    for match in found_matches:
                        line_num = code[:match.start()].count('\n') + 1
                        
                        # Determine severity based on pattern type
                        severity = self._determine_pattern_severity(category, match.group())
                        
                        matches.append({
                            "line": line_num,
                            "code": match.group().strip(),
                            "pattern": pattern,
                            "severity": severity,
                            "category": category
                        })
                        
                        # Update severity breakdown
                        findings["severity_breakdown"][severity] += 1
                
                if matches:
                    findings["pattern_matches"][category] = matches
                    findings["total_issues"] += len(matches)
            
            # Calculate performance score
            findings["performance_score"] = self._calculate_performance_score(findings["severity_breakdown"])
            
            return findings
            
        except Exception as e:
            logger.error(f"❌ Performance pattern analysis failed: {e}")
            return {"error": str(e), "pattern_matches": {}, "performance_score": 0}
    
    def _determine_pattern_severity(self, category: str, code_match: str) -> str:
        """Determine severity of performance issue based on pattern and context"""
        # Check for large numbers that indicate high impact
        large_number_pattern = re.search(r'\d{6,}', code_match)
        if large_number_pattern:
            number = int(large_number_pattern.group())
            if number >= 1000000:
                return "critical"
            elif number >= 100000:
                return "high"
            else:
                return "medium"
        
        # Category-based severity
        critical_categories = ["memory_issues", "dom_performance"]
        high_categories = ["inefficient_loops", "string_concatenation"]
        
        if category in critical_categories:
            return "critical" if large_number_pattern else "high"
        elif category in high_categories:
            return "high" if large_number_pattern else "medium"
        else:
            return "medium"
    
    def _calculate_performance_score(self, severity_breakdown: Dict[str, int]) -> int:
        """Calculate performance score based on issue severity"""
        score = 10
        score -= severity_breakdown["critical"] * 3
        score -= severity_breakdown["high"] * 2
        score -= severity_breakdown["medium"] * 1
        score -= severity_breakdown["low"] * 0.5
        
        return max(0, int(score))
    
    async def analyze_performance_detailed(self, code: str, language: str) -> Dict[str, Any]:
        """Detailed performance analysis using Gemini Pro"""
        try:
            performance_prompt = f"""
            Perform comprehensive performance analysis of this {language} code:
            
            ```
            {code}
            ```
            
            Analyze for:
            
            1. **ALGORITHMIC COMPLEXITY:**
            - Time complexity (Big O notation)
            - Space complexity
            - Nested loops and their impact
            - Recursive function efficiency
            
            2. **MEMORY USAGE:**
            - Memory leaks and excessive allocation
            - Large data structures
            - Inefficient data structure choices
            - Memory optimization opportunities
            
            3. **I/O OPERATIONS:**
            - File I/O efficiency
            - Database query optimization
            - Network request optimization
            - Caching opportunities
            
            4. **LANGUAGE-SPECIFIC OPTIMIZATIONS:**
            {self._get_language_specific_performance_checks(language)}
            
            5. **CONCURRENCY & ASYNC:**
            - Blocking operations that could be async
            - Thread safety issues
            - Parallelization opportunities
            
            For each issue found, provide:
            - **Severity**: Critical/High/Medium/Low
            - **Impact**: Performance degradation estimate
            - **Location**: Specific line numbers
            - **Current Complexity**: Big O analysis
            - **Optimization**: Specific code improvements
            - **Expected Improvement**: Performance gain estimate
            
            Provide performance score (1-10) and prioritized optimization recommendations.
            """
            
            response = await self.gemini_client.complex_model.ainvoke([{"role": "user", "content": performance_prompt}])
            
            return {
                "analysis_type": "detailed_performance",
                "language": language,
                "model_used": "gemini-2.5-pro", 
                "detailed_analysis": response.content,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"❌ Detailed performance analysis failed: {e}")
            return {
                "error": str(e),
                "analysis_type": "failed_performance"
            }
    
    def _get_language_specific_performance_checks(self, language: str) -> str:
        """Get language-specific performance optimization guidelines"""
        checks = {
            "python": """
            - List comprehensions vs loops
            - Generator expressions for large datasets
            - Built-in functions (sum, max, min) vs manual loops
            - String concatenation methods
            - Dictionary lookups vs list searches
            - NumPy array operations for numerical computations
            """,
            "javascript": """
            - DOM manipulation optimization
            - Event delegation vs multiple listeners
            - Array methods (map, filter, reduce) efficiency
            - String template literals vs concatenation
            - Object property access patterns
            - Async/await vs Promise chains
            """,
            "java": """
            - Collection framework efficiency
            - String vs StringBuilder for concatenation
            - Stream API vs traditional loops
            - Memory management and garbage collection
            - Synchronization overhead
            - Boxing/unboxing performance
            """
        }
        
        return checks.get(language, "- General optimization patterns")
    
    async def analyze_file_performance(self, file_path: str, code_content: str, language: str) -> Dict[str, Any]:
        """Complete performance analysis combining patterns and AI analysis"""
        try:
            logger.info(f"⚡ Running performance analysis on {file_path}")
            
            # Run both pattern matching and detailed AI analysis
            pattern_results, detailed_results = await asyncio.gather(
                self.analyze_performance_patterns(code_content, language),
                self.analyze_performance_detailed(code_content, language)
            )
            
            # Combine results
            performance_report = {
                "file_path": file_path,
                "language": language,
                "analysis_timestamp": asyncio.get_event_loop().time(),
                "pattern_analysis": pattern_results,
                "detailed_analysis": detailed_results,
                "summary": {
                    "performance_score": pattern_results.get("performance_score", 0),
                    "total_issues": pattern_results.get("total_issues", 0),
                    "severity_breakdown": pattern_results.get("severity_breakdown", {}),
                    "has_detailed_analysis": "error" not in detailed_results,
                    "critical_issues": pattern_results.get("severity_breakdown", {}).get("critical", 0)
                }
            }
            
            return performance_report
            
        except Exception as e:
            logger.error(f"❌ Complete performance analysis failed for {file_path}: {e}")
            return {
                "file_path": file_path,
                "error": str(e),
                "analysis_type": "failed"
            }

# Global instance
performance_agent = None

def get_performance_agent() -> PerformanceAnalysisAgent:
    """Get or create global performance agent instance"""
    global performance_agent
    if performance_agent is None:
        performance_agent = PerformanceAnalysisAgent()
    return performance_agent
