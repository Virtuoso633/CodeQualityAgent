"""
Streamlit Frontend for Code Quality Intelligence Agent
Professional dashboard with advanced visualizations and REAL context integration
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Configure Streamlit
st.set_page_config(
    page_title="🤖 Code Quality Intelligence",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .status-processing {
        color: #ff9500;
        font-weight: bold;
    }
    
    .status-completed {
        color: #34c759;
        font-weight: bold;
    }
    
    .status-failed {
        color: #ff3b30;
        font-weight: bold;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%);
        color: white;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #2193b0, #6dd5ed);
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
try:
    API_BASE_URL = st.secrets["API_BASE_URL"]
except Exception:
    API_BASE_URL = "http://localhost:8000"  # Fallback for local development

# Session state initialization
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "analysis_ready" not in st.session_state:
    st.session_state.analysis_ready = False
if "current_analysis_id" not in st.session_state:
    st.session_state.current_analysis_id = None
if "comprehensive_analysis_ready" not in st.session_state:
    st.session_state.comprehensive_analysis_ready = False

def make_api_request(endpoint: str, method: str = "GET", data: Dict = None, files: Any = None):
    """Make API request with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, data=data, files=files)
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return None

def display_main_header():
    """Display main header with branding"""
    st.markdown('<div class="main-header">🤖 Code Quality Intelligence Agent</div>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    ### 🚀 AI-Powered Code Analysis Platform
    **Multi-Agent Coordination • RAG-Enhanced Understanding • Interactive Q&A with REAL Context**
    
    ---
    """)

# ... [All original display functions remain here, unchanged] ...
# (display_analysis_metrics, create_quality_radar_chart, display_quality_insights, etc.)
def display_analysis_metrics(results: Dict[str, Any]):
    """Display analysis metrics in an attractive layout"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if "summary" in results:
            st.metric("📊 Files Analyzed", results["summary"].get("total_files", "N/A"))
        else:
            st.metric("📊 Files Analyzed", results.get("files_analyzed", "N/A"))
    
    with col2:
        if "summary" in results:
            st.metric("🔤 Languages Found", len(results["summary"].get("languages_found", [])))
        else:
            st.metric("🔤 Languages", len(results.get("languages_detected", [])))
    
    with col3:
        if "summary" in results:
            total_issues = results["summary"].get("total_issues", 0)
            st.metric("📈 Total Issues", total_issues, delta="Critical" if total_issues > 0 else "Clean")
        else:
            st.metric("📈 Total Issues", results.get("total_issues", "N/A"))
    
    with col4:
        if "summary" in results:
            processing_time = results["summary"].get("processing_time", 0)
            st.metric("⏱️ Processing Time", f"{processing_time:.2f}s")
        else:
            st.metric("⏱️ Processing Time", "N/A")

def create_quality_radar_chart(results: Dict[str, Any]) -> go.Figure:
    """Create INTERACTIVE radar chart with real data and user-friendly tooltips"""
    
    # Define categories with descriptions for tooltips
    categories = ['Security', 'Performance', 'Maintainability', 'Architecture', 'Testing', 'Documentation']
    
    descriptions = {
        'Security': 'Hardcoded secrets, input validation, injection vulnerabilities',
        'Performance': 'Memory usage, algorithmic efficiency, optimization opportunities',
        'Maintainability': 'Code readability, comments, modularity, complexity',
        'Architecture': 'Design patterns, SOLID principles, structure',
        'Testing': 'Test coverage, assertions, edge cases, automation',
        'Documentation': 'Docstrings, README, usage guides, API docs'
    }
    
    # Initialize with good default scores (will be reduced based on issues)
    scores = [8, 7, 6, 7, 5, 6]  # Out of 10
    issue_counts = [0, 0, 0, 0, 0, 0]
    specific_issues = {cat: [] for cat in categories}
    
    # Extract REAL data from analysis results
    if results and "detailed_results" in results:
        for filename, file_result in results["detailed_results"].items():
            issues = file_result.get("issues_found", [])
            
            for issue in issues:
                issue_type = issue.get("type", "")
                severity = issue.get("severity", "medium")
                
                # Map issue types to radar categories
                if issue_type == "security":
                    # Reduce security score based on severity
                    reduction = 3 if severity == "critical" else 2 if severity == "high" else 1
                    scores[0] = max(1, scores[0] - reduction)
                    issue_counts[0] += 1
                    specific_issues['Security'].append(f"Line {issue.get('line', '?')}: {issue.get('issue', 'Security issue')}")
                    
                elif issue_type == "performance":
                    reduction = 2 if severity == "high" else 1
                    scores[1] = max(1, scores[1] - reduction)
                    issue_counts[1] += 1
                    specific_issues['Performance'].append(f"Line {issue.get('line', '?')}: {issue.get('issue', 'Performance issue')}")
                    
                elif issue_type == "quality":
                    scores[2] = max(1, scores[2] - 1)
                    issue_counts[2] += 1
                    specific_issues['Maintainability'].append(f"Line {issue.get('line', '?')}: {issue.get('issue', 'Quality issue')}")
    
    # Create hover text with detailed information
    hover_texts = []
    display_texts = []
    
    for i, category in enumerate(categories):
        score = scores[i]
        issues = issue_counts[i]
        
        # Create detailed hover information
        hover_info = f"<b>{category}</b><br>"
        hover_info += f"Score: {score}/10<br>"
        hover_info += f"Issues Found: {issues}<br>"
        hover_info += f"<br><i>{descriptions[category]}</i>"
        
        if specific_issues[category]:
            hover_info += f"<br><br><b>Specific Issues:</b><br>"
            for issue in specific_issues[category][:3]:  # Show max 3 issues
                hover_info += f"• {issue}<br>"
            if len(specific_issues[category]) > 3:
                hover_info += f"• ... and {len(specific_issues[category]) - 3} more"
        
        hover_texts.append(hover_info)
        display_texts.append(f"{score}")
    
    # Create the radar chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        name='Code Quality',
        line=dict(color='rgba(67, 176, 209, 0.8)', width=3),
        marker=dict(
            size=10,
            color='rgba(67, 176, 209, 0.9)',
            line=dict(color='white', width=2)
        ),
        mode='lines+markers+text',
        text=display_texts,
        textposition="middle center",
        textfont=dict(size=12, color='white'),
        hovertemplate='%{hovertext}<extra></extra>',
        hovertext=hover_texts
    ))
    
    # Add a reference line showing "good" scores
    reference_scores = [8, 8, 8, 8, 8, 8]
    fig.add_trace(go.Scatterpolar(
        r=reference_scores,
        theta=categories,
        mode='lines',
        line=dict(color='rgba(128, 128, 128, 0.3)', width=1, dash='dot'),
        name='Target Quality',
        showlegend=True,
        hovertemplate='Target Score: 8/10<extra></extra>'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickfont=dict(size=11),
                gridcolor='rgba(128, 128, 128, 0.2)'
            ),
            angularaxis=dict(
                tickfont=dict(size=12)
            )
        ),
        title=dict(
            text="📊 Interactive Code Quality Analysis",
            font=dict(size=16),
            x=0.5
        ),
        font=dict(size=12),
        height=500,
        margin=dict(l=60, r=60, t=80, b=40),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left", 
            x=0.01
        )
    )
    
    return fig

def display_quality_insights(results: Dict[str, Any]):
    """Display contextual information about the quality analysis"""
    
    if not results or "detailed_results" not in results:
        st.info("📈 Upload and analyze code files to see detailed quality metrics here!")
        return
    
    # Calculate summary statistics
    total_files = len(results["detailed_results"])
    total_issues = 0
    critical_issues = 0
    issue_breakdown = {"security": 0, "performance": 0, "quality": 0}
    
    for file_result in results["detailed_results"].values():
        for issue in file_result.get("issues_found", []):
            total_issues += 1
            if issue.get("severity") == "critical":
                critical_issues += 1
            issue_type = issue.get("type", "other")
            if issue_type in issue_breakdown:
                issue_breakdown[issue_type] += 1
    
    # Display insights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Files Analyzed", total_files)
        
    with col2:
        st.metric("Total Issues", total_issues, delta=f"{critical_issues} critical")
        
    with col3:
        overall_score = 8 - min(6, total_issues)  # Simple scoring
        st.metric("Overall Score", f"{overall_score}/10")
    
    # Priority recommendations
    if critical_issues > 0:
        st.error(f"🚨 **URGENT**: {critical_issues} critical security issues found. Fix immediately!")
    elif total_issues > 5:
        st.warning("⚠️ **HIGH PRIORITY**: Multiple issues detected. Focus on security and performance first.")
    elif total_issues > 0:
        st.info(f"💡 **IMPROVEMENT OPPORTUNITY**: {total_issues} issues found. Address when convenient.")
    else:
        st.success("✅ **EXCELLENT**: No major issues detected in your code!")

def display_enhanced_analysis_dashboard():
    """Display enhanced analysis with interactive radar chart"""
    
    if st.session_state.get("analysis_results"):
        results = st.session_state.analysis_results
        
        # Show quality insights
        display_quality_insights(results)
        
        st.markdown("---")
        
        # Show interactive radar chart
        st.subheader("📊 Quality Breakdown")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Create and display the enhanced radar chart
            radar_fig = create_quality_radar_chart(results)
            st.plotly_chart(radar_fig, use_container_width=True)
        
        with col2:
            st.markdown("### 📋 How to Read This Chart")
            st.markdown("""
            **🎯 Scores (0-10):**
            - **8-10**: Excellent
            - **6-7**: Good  
            - **4-5**: Needs improvement
            - **1-3**: Critical issues
            
            **💡 Interactive Features:**
            - **Hover** over points for details
            - **Click** legend to toggle views
            - **Zoom** and pan as needed
            
            **🔍 Categories Explained:**
            - **Security**: Vulnerabilities and risks
            - **Performance**: Speed and efficiency  
            - **Maintainability**: Code readability
            - **Architecture**: Structure and design
            - **Testing**: Coverage and quality
            - **Documentation**: Comments and guides
            """)
    
    else:
        st.info("👆 Upload files or analyze a GitHub repository to see interactive quality insights!")
        
        # Show demo chart
        st.subheader("📊 Sample Dashboard")
        demo_results = {
            "detailed_results": {
                "example.py": {
                    "issues_found": [
                        {"type": "security", "severity": "critical", "line": 9, "issue": "Hardcoded password"},
                        {"type": "performance", "severity": "high", "line": 10, "issue": "Large memory allocation"}
                    ]
                }
            }
        }
        demo_fig = create_quality_radar_chart(demo_results)
        st.plotly_chart(demo_fig, use_container_width=True)

def display_file_analysis_results():
    """Display real analysis results with chat integration"""
    if "current_analysis_id" in st.session_state and st.session_state.current_analysis_id:
        analysis_id = st.session_state.current_analysis_id
        
        # Check analysis status
        status_response = make_api_request(f"/analyze/{analysis_id}/status")
        
        if status_response and status_response.get("status") == "completed":
            st.success("✅ Analysis completed! You can now ask questions about your code.")
            
            results = status_response.get("results", {})
            if results:
                # Store results in session state
                st.session_state.analysis_results = results
                
                # Display metrics
                display_analysis_metrics(results)
                
                st.subheader("📊 Analysis Summary")
                
                # Show detailed results if available
                if "detailed_results" in results:
                    detailed_results = results["detailed_results"]
                    
                    # Show file-by-file results
                    for filename, result in detailed_results.items():
                        with st.expander(f"📄 {filename} ({result.get('language', 'unknown')})"):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                if 'issues_found' in result and result['issues_found']:
                                    st.markdown("**🔍 Issues Found:**")
                                    for issue in result['issues_found']:
                                        severity_colors = {
                                            "critical": "🔴", 
                                            "high": "🟠", 
                                            "medium": "🟡", 
                                            "low": "🟢"
                                        }
                                        severity_color = severity_colors.get(issue['severity'], '⚪')
                                        
                                        st.markdown(f"{severity_color} **Line {issue['line']}** ({issue['severity'].upper()}): {issue['issue']}")
                                        st.code(issue['code'], language=result.get('language', 'text'))
                                        st.markdown("---")
                                else:
                                    st.success("✅ No major issues found in this file")
                            
                            with col2:
                                st.markdown("**📈 File Stats:**")
                                st.metric("File Size", f"{result.get('size', 0)} chars")
                                st.metric("Language", result.get('language', 'Unknown'))
                                
                                if 'issues_found' in result:
                                    issue_count = len(result['issues_found'])
                                    st.metric("Issues", issue_count, delta="⚠️" if issue_count > 0 else "✅")
                
                # Enable contextual chat
                st.session_state.analysis_ready = True
                
        elif status_response and status_response.get("status") == "processing":
            st.info("🔄 Analysis in progress...")
            # Auto-refresh every 3 seconds
            time.sleep(3)
            st.rerun()
        elif status_response and status_response.get("status") == "analyzing":
            st.warning("🔍 Analyzing your code... This may take a few moments.")
            time.sleep(3)
            st.rerun()
        elif status_response and status_response.get("status") == "failed":
            st.error(f"❌ Analysis failed: {status_response.get('error', 'Unknown error')}")
            st.session_state.current_analysis_id = None

def enhanced_chat_interface():
    """Enhanced chat that uses actual analysis context"""  
    st.subheader("💬 Ask About Your Code")
    
    if not st.session_state.get("analysis_ready", False) and not st.session_state.get("comprehensive_analysis_ready", False):
        st.warning("⚠️ Analyze a codebase first to enable contextual chat!")
        st.info("""
        **Once analysis is complete, you can ask questions like:**
        - "What security issues are in my code?"
        - "How can I improve performance?"
        - "What's wrong with line 25 in my Python file?"
        - "Show me all critical issues"
        """)
        return
    
    # Display current context info
    if st.session_state.analysis_results:
        with st.expander("📋 Current Analysis Context"):
            results = st.session_state.analysis_results
            if "detailed_results" in results: # Simple analysis
                analyzed_files = list(results["detailed_results"].keys())
                st.success(f"🎯 Context Available: {len(analyzed_files)} files analyzed")
            elif "file_analyses" in results: # Comprehensive analysis
                analyzed_files = list(results["file_analyses"].keys())
                st.success(f"🎯 Context Available: {len(analyzed_files)} files from codebase analyzed")

            st.markdown("**Files in context:**")
            for filename in analyzed_files[:10]: # Show first 10
                st.markdown(f"- 📄 {filename}")
            if len(analyzed_files) > 10:
                st.markdown(f"- ... and {len(analyzed_files) - 10} more files.")

    # Display chat history with better formatting
    if st.session_state.chat_messages:
        st.markdown("### 💬 Conversation History")
        for message in st.session_state.chat_messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 You:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                content_with_breaks = message["content"].replace('\n', '<br>')
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>🤖 AI Assistant:</strong><br>
                    {content_with_breaks}
                </div>
                """, unsafe_allow_html=True)
    
    # Chat input form
    with st.form("contextual_chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            prompt = st.text_input(
                "Ask about your analyzed code:",
                placeholder="e.g., What security issues should I fix first?",
                key="contextual_chat_input"
            )
        
        with col2:
            submit_button = st.form_submit_button("🚀 Send", type="primary")
        
        # Quick question buttons
        st.markdown("**🔥 Quick Questions:**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.form_submit_button("🛡️ Security Issues"):
                prompt = "What security issues are in my code?"
                submit_button = True
        
        with col2:
            if st.form_submit_button("⚡ Performance"):
                prompt = "How can I improve performance?"
                submit_button = True
        
        with col3:
            if st.form_submit_button("🔧 Code Quality"):
                prompt = "What quality issues should I fix?"
                submit_button = True
        
        with col4:
            if st.form_submit_button("📊 Summary"):
                prompt = "Give me a summary of all issues"
                submit_button = True
    
    # Process chat query
    if submit_button and prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        with st.spinner("🤖 Thinking with context..."):
            response = make_api_request(
                "/chat/query",
                method="POST", 
                data=json.dumps({
                    "query": prompt,
                    "session_id": st.session_state.session_id
                })
            )
            
            if response and response.get("status") == "success":
                answer = response["response"]["answer"]
                st.session_state.chat_messages.append({"role": "assistant", "content": answer})
                st.rerun()
            else:
                st.error("❌ Failed to get response from AI assistant")

def enhanced_upload_section():
    """Enhanced upload for simple, multi-file analysis"""
    st.subheader("📤 Quick Upload & Analysis")
    st.markdown("Upload individual code files for a fast, focused analysis.")
    
    uploaded_files = st.file_uploader(
        "Choose your code files:",
        type=['py', 'js', 'java', 'ts', 'jsx', 'tsx'],
        accept_multiple_files=True,
        help="Upload Python, JavaScript, Java, or TypeScript files for analysis"
    )
    
    if uploaded_files:
        st.success(f"📁 {len(uploaded_files)} files ready for upload:")
        for file in uploaded_files:
            st.markdown(f"- 📄 **{file.name}** ({file.type})")
    
    if st.button("🚀 Analyze Files", type="primary", disabled=not uploaded_files):
        with st.spinner("🔄 Uploading and analyzing your files..."):
            files_for_upload = [("files", (file.name, file.getvalue(), file.type)) for file in uploaded_files]
            
            response = make_api_request(
                "/analyze/upload",
                method="POST",
                data={"analysis_type": "comprehensive", "include_rag": "True"},
                files=files_for_upload
            )
            
            if response and response.get("status") == "processing":
                analysis_id = response["analysis_id"]
                st.session_state.current_analysis_id = analysis_id
                st.session_state.analysis_results = {}
                st.session_state.chat_messages = []
                st.session_state.analysis_ready = False
                st.session_state.comprehensive_analysis_ready = False
                
                st.success(f"✅ Upload successful! Analysis ID: `{analysis_id}`")
                st.rerun()
            else:
                st.error("❌ Upload failed. Please check your connection and try again.")

# --- NEW COMPREHENSIVE ANALYSIS FUNCTIONS ---

def get_all_supported_extensions():
    """Static list of supported extensions for the frontend uploader."""
    return [
        'py', 'java', 'js', 'ts', 'tsx', 'jsx', 'cs', 'cpp', 'h', 'hpp', 
        'go', 'rs', 'php', 'rb', 'swift', 'kt', 'kts'
    ]

def create_comprehensive_radar_chart(scores: Dict):
    """Placeholder for the comprehensive radar chart."""
    st.info("Comprehensive radar chart will be displayed here.")
    # In a real implementation, you would use Plotly to draw a chart from the scores dict.
    return go.Figure()

def display_security_findings(results: Dict):
    """Placeholder for displaying security findings."""
    st.info("Detailed security findings will be displayed here.")

def display_performance_findings(results: Dict):
    """Placeholder for displaying performance findings."""
    st.info("Detailed performance findings will be displayed here.")
    
def display_quality_findings(results: Dict):
    """Placeholder for displaying quality findings."""
    st.info("Detailed code quality findings will be displayed here.")

def display_architecture_findings(results: Dict):
    """Placeholder for displaying architecture findings."""
    st.info("Detailed architecture findings will be displayed here.")

def display_duplicate_findings(results: Dict):
    """Placeholder for displaying code duplication findings."""
    st.info("Code duplication analysis results will be displayed here.")

def comprehensive_analysis_interface():
    """Interface for comprehensive codebase analysis"""
    st.subheader("🏗️ Comprehensive Codebase Analysis")
    st.markdown("Analyze entire repositories with deep multi-language understanding")
    
    analysis_mode = st.radio(
        "Analysis Mode",
        ["🌐 GitHub Repository", "📤 Upload Project Files"],
        horizontal=True
    )
    
    if analysis_mode == "🌐 GitHub Repository":
        github_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/owner/repository"
        )
        
        with st.expander("🔧 Advanced Options"):
            analyze_architecture = st.checkbox("Analyze architecture patterns", value=True)
            detect_duplicates = st.checkbox("Detect code duplicates", value=True)
        
        if st.button("🚀 Analyze Repository", type="primary", disabled=not github_url):
            if github_url and github_url.startswith("https://github.com/"):
                options = {
                    "analyze_architecture": analyze_architecture,
                    "detect_duplicates": detect_duplicates,
                }
                
                with st.spinner("🔄 Starting comprehensive repository analysis..."):
                    response = make_api_request(
                        "/analyze/comprehensive",
                        method="POST",
                        data={
                            "github_url": github_url,
                            "analysis_options": json.dumps(options)
                        }
                    )
                    
                    if response and response.get("status") == "processing":
                        analysis_id = response["analysis_id"]
                        st.session_state.current_analysis_id = analysis_id
                        st.success(f"✅ Comprehensive analysis started! ID: {analysis_id}")
                        st.info("This may take several minutes for large repositories...")
                        st.rerun()
            else:
                st.error("Please enter a valid GitHub repository URL")
    
    else: # Upload Project Files
        st.info("💡 Tip: You can upload all files from a project folder for a full analysis.")
        
        uploaded_files = st.file_uploader(
            "Choose all code files from your project",
            type=get_all_supported_extensions(),
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.success(f"📁 {len(uploaded_files)} files selected for analysis.")
            
            if st.button("🔍 Analyze Codebase", type="primary"):
                with st.spinner("🔄 Analyzing entire codebase... This may take a while."):
                    files_for_upload = [("files", (file.name, file.getvalue(), file.type)) for file in uploaded_files]
                    
                    response = make_api_request(
                        "/analyze/comprehensive",
                        method="POST",
                        data={"analysis_options": "{}"},
                        files=files_for_upload
                    )
                    
                    if response and response.get("status") == "processing":
                        analysis_id = response["analysis_id"]
                        st.session_state.current_analysis_id = analysis_id
                        st.success(f"✅ Comprehensive analysis started!")
                        st.rerun()

def display_comprehensive_dashboard(results: Dict):
    """Display comprehensive analysis dashboard"""
    st.success("🎉 Comprehensive Analysis Complete!")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📁 Total Files", results.get("total_files", 0))
    with col2:
        languages = results.get("languages_detected", {})
        st.metric("🔤 Languages", len(languages))
    with col3:
        scores = results.get("overall_scores", {})
        overall_score = scores.get("overall", 0)
        st.metric("🏆 Overall Score", f"{overall_score}/10")
    with col4:
        st.metric("🔍 Total Issues", results.get("total_issues", "N/A"))

    tab1, tab2 = st.columns(2)
    with tab1:
        if languages:
            st.subheader("📊 Language Distribution")
            lang_df = pd.DataFrame(list(languages.items()), columns=["Language", "Files"])
            fig = px.pie(lang_df, values="Files", names="Language", title="Files by Language")
            st.plotly_chart(fig, use_container_width=True)
    with tab2:
        if scores:
            st.subheader("📈 Quality Metrics")
            radar_fig = create_comprehensive_radar_chart(scores)
            st.plotly_chart(radar_fig, use_container_width=True)
            
    st.subheader("🔍 Detailed Findings")
    sec_tab, perf_tab, qual_tab, arch_tab, dup_tab = st.tabs([
        "🛡️ Security", "⚡ Performance", "🔧 Quality", "🏗️ Architecture", "📋 Duplicates"
    ])
    
    with sec_tab: display_security_findings(results)
    with perf_tab: display_performance_findings(results)
    with qual_tab: display_quality_findings(results)
    with arch_tab: display_architecture_findings(results)
    with dup_tab: display_duplicate_findings(results)

def display_comprehensive_results():
    """Display comprehensive analysis results"""
    if not st.session_state.get("current_analysis_id"):
        return
    
    analysis_id = st.session_state.current_analysis_id
    status_response = make_api_request(f"/analyze/{analysis_id}/status")
    
    if not status_response:
        st.error("Could not fetch analysis status.")
        return
    
    status = status_response.get("status")
    
    if status == "processing" or status == "cloning" or status == "analyzing":
        st.info(f"🔄 Analysis in progress... (Status: {status}). This may take several minutes.")
        st.progress(int(status_response.get("progress", 0)))
        time.sleep(5)
        st.rerun()
    elif status == "completed":
        results = status_response.get("results", {})
        st.session_state.analysis_results = results
        if results:
            display_comprehensive_dashboard(results)
            st.session_state.comprehensive_analysis_ready = True
    elif status == "failed":
        st.error(f"❌ Analysis failed: {status_response.get('error', 'Unknown error')}")


def main():
    """Main Streamlit app with integrated features"""
    display_main_header()
    
    with st.sidebar:
        st.markdown("## 🎛️ Control Panel")
        health = make_api_request("/health")
        if health and health.get("status") == "healthy":
            st.success("✅ API Connected")
        else:
            st.error("❌ API Disconnected")
        
        st.markdown("---")
        st.markdown("### 📊 Session Info")
        st.info(f"**Session ID:** `{st.session_state.session_id[:8]}...`")
        if st.session_state.current_analysis_id:
            st.success(f"**Analysis:** `{st.session_state.current_analysis_id[:8]}...`")
        
        st.markdown("---")
        page = st.selectbox(
            "📍 Navigate",
            ["🏗️ Comprehensive Analysis", "📤 Quick Upload", "💬 Interactive Chat", "📈 Analytics"]
        )
    
    if page == "🏗️ Comprehensive Analysis":
        comprehensive_analysis_interface()
        st.markdown("---")
        st.subheader("📊 Analysis Results")
        if st.session_state.current_analysis_id and st.session_state.get('analysis_results', {}).get('comprehensive'):
             display_comprehensive_results()
        else:
            display_comprehensive_results() # Handles status checking
            
    elif page == "📤 Quick Upload":
        enhanced_upload_section()
        if st.session_state.current_analysis_id and not st.session_state.get('analysis_results', {}).get('comprehensive'):
            st.markdown("---")
            st.subheader("📊 Analysis Results")
            display_file_analysis_results()

    elif page == "💬 Interactive Chat":
        enhanced_chat_interface()
    
    elif page == "📈 Analytics":
        st.markdown("## 📈 Platform Analytics")
        analytics = make_api_request("/analytics/stats")
        if analytics:
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Total Analyses", analytics.get("total_analyses", 0))
            with col2: st.metric("Completed", analytics.get("completed_analyses", 0))
            with col3: st.metric("Contextual Analyses", analytics.get("contextual_analyses", 0))
            with col4: st.metric("Success Rate", f"{analytics.get('success_rate', 0):.1%}")

if __name__ == "__main__":
    main()