"""
Specialized Security Analysis Agent
"""
import asyncio
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from models.gemini.gemini_client import get_gemini_client
from config.settings import QUALITY_CATEGORIES

logger = logging.getLogger(__name__)

class SecurityAnalysisAgent:
    """Specialized agent for security vulnerability analysis"""
    
    def __init__(self):
        """Initialize security agent with Gemini models"""
        self.gemini_client = get_gemini_client()
        self.security_patterns = {
            "python": {
                "sql_injection": [
                    r"execute\s*\(\s*['\"].+%s.+['\"]",
                    r"\.format\s*\(",
                    r"cursor\.execute\s*\(\s*f['\"]"
                ],
                "hardcoded_secrets": [
                    r"password\s*=\s*['\"][^'\"]+['\"]",
                    r"api_key\s*=\s*['\"][^'\"]+['\"]",
                    r"secret\s*=\s*['\"][^'\"]+['\"]",
                    r"token\s*=\s*['\"][^'\"]+['\"]"
                ],
                "unsafe_eval": [
                    r"\beval\s*\(",
                    r"\bexec\s*\(",
                    r"subprocess\.(call|run|Popen).*shell\s*=\s*True"
                ],
                "weak_crypto": [
                    r"md5\(",
                    r"sha1\(",
                    r"DES\(",
                    r"random\.random\("
                ]
            },
            "javascript": {
                "xss_vulnerable": [
                    r"innerHTML\s*=",
                    r"document\.write\s*\(",
                    r"eval\s*\("
                ],
                "hardcoded_secrets": [
                    r"password\s*[:=]\s*['\"][^'\"]+['\"]",
                    r"apiKey\s*[:=]\s*['\"][^'\"]+['\"]",
                    r"secret\s*[:=]\s*['\"][^'\"]+['\"]"
                ],
                "unsafe_operations": [
                    r"eval\s*\(",
                    r"Function\s*\(",
                    r"setTimeout\s*\(\s*['\"]"
                ]
            }
        }
    
    async def analyze_security_patterns(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code using pattern matching for common vulnerabilities"""
        try:
            findings = {
                "pattern_matches": {},
                "risk_level": "low",
                "total_issues": 0
            }
            
            if language not in self.security_patterns:
                return findings
            
            # Check each security pattern category
            for category, patterns in self.security_patterns[language].items():
                matches = []
                
                for pattern in patterns:
                    found_matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
                    for match in found_matches:
                        line_num = code[:match.start()].count('\n') + 1
                        matches.append({
                            "line": line_num,
                            "code": match.group().strip(),
                            "pattern": pattern
                        })
                
                if matches:
                    findings["pattern_matches"][category] = matches
                    findings["total_issues"] += len(matches)
            
            # Determine overall risk level
            if findings["total_issues"] >= 5:
                findings["risk_level"] = "critical"
            elif findings["total_issues"] >= 3:
                findings["risk_level"] = "high"
            elif findings["total_issues"] >= 1:
                findings["risk_level"] = "medium"
            
            return findings
            
        except Exception as e:
            logger.error(f"❌ Pattern analysis failed: {e}")
            return {"error": str(e), "pattern_matches": {}, "total_issues": 0}
    
    async def analyze_security_detailed(self, code: str, language: str) -> Dict[str, Any]:
        """Detailed security analysis using Gemini Pro"""
        try:
            security_prompt = f"""
            Perform comprehensive security analysis of this {language} code:
            
            ```
            {code}
            ```
            
            Analyze for:
            
            1. **OWASP TOP 10 VULNERABILITIES:**
            - Injection attacks (SQL, NoSQL, Command, etc.)
            - Broken Authentication & Session Management
            - Sensitive Data Exposure
            - XML External Entities (XXE)
            - Broken Access Control
            - Security Misconfiguration
            - Cross-Site Scripting (XSS)
            - Insecure Deserialization
            - Known Vulnerable Components
            - Insufficient Logging & Monitoring
            
            2. **LANGUAGE-SPECIFIC SECURITY ISSUES:**
            - Buffer overflows, memory leaks
            - Type confusion attacks
            - Race conditions
            - Path traversal vulnerabilities
            
            3. **CRYPTOGRAPHIC ISSUES:**
            - Weak encryption algorithms
            - Poor key management
            - Insecure random number generation
            - Hash collisions
            
            4. **INPUT VALIDATION:**
            - Unvalidated user input
            - Missing sanitization
            - Improper encoding/decoding
            
            For each issue found, provide:
            - **Severity Level**: Critical/High/Medium/Low
            - **Vulnerability Type**: OWASP category
            - **Location**: Line numbers if possible
            - **Impact**: What could happen if exploited
            - **Remediation**: Specific code fixes with examples
            - **Prevention**: How to avoid similar issues
            
            Format as structured, actionable security report.
            """
            
            response = await self.gemini_client.complex_model.ainvoke([{"role": "user", "content": security_prompt}])
            
            return {
                "analysis_type": "detailed_security",
                "language": language,
                "model_used": "gemini-2.5-pro",
                "detailed_analysis": response.content,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"❌ Detailed security analysis failed: {e}")
            return {
                "error": str(e),
                "analysis_type": "failed_security"
            }
    
    async def analyze_file_security(self, file_path: str, code_content: str, language: str) -> Dict[str, Any]:
        """Complete security analysis combining patterns and AI analysis"""
        try:
            logger.info(f"🔒 Running security analysis on {file_path}")
            
            # Run both pattern matching and detailed AI analysis
            pattern_results, detailed_results = await asyncio.gather(
                self.analyze_security_patterns(code_content, language),
                self.analyze_security_detailed(code_content, language)
            )
            
            # Combine results
            security_report = {
                "file_path": file_path,
                "language": language,
                "analysis_timestamp": asyncio.get_event_loop().time(),
                "pattern_analysis": pattern_results,
                "detailed_analysis": detailed_results,
                "summary": {
                    "total_pattern_matches": pattern_results.get("total_issues", 0),
                    "risk_level": pattern_results.get("risk_level", "low"),
                    "has_detailed_analysis": "error" not in detailed_results,
                    "categories_found": list(pattern_results.get("pattern_matches", {}).keys())
                }
            }
            
            return security_report
            
        except Exception as e:
            logger.error(f"❌ Complete security analysis failed for {file_path}: {e}")
            return {
                "file_path": file_path,
                "error": str(e),
                "analysis_type": "failed"
            }

# Global instance
security_agent = None

def get_security_agent() -> SecurityAnalysisAgent:
    """Get or create global security agent instance"""
    global security_agent
    if security_agent is None:
        security_agent = SecurityAnalysisAgent()
    return security_agent
