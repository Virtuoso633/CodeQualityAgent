"""
Streamlit Frontend for Code Quality Intelligence Agent - FINAL POLISHED & AI-DRIVEN
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json
import time
import uuid
from typing import Dict, Any
import os
from pathlib import Path

# --- Page Configuration ---
st.set_page_config(page_title="CodeIQ 🤖", page_icon="🤖", layout="wide")

# --- Enhanced Custom Styling ---
st.markdown("""
<style>
    .stApp { background-color: #1a1a2e; }
    h1, h2, h3 { color: #e0e0e0; }
    .main-header {
        font-size: 3rem; font-weight: bold; text-align: center; margin-bottom: 2rem;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    .info-box {
        background-color: #2c2c54; border-radius: 10px; padding: 1rem;
        border-left: 5px solid #4d4dff; margin: 1rem 0; color: #e0e0e0;
    }
    .info-box.rag { border-left-color: #20c997; }
    .metric-card {
        background-color: #262730; border-radius: 10px; padding: 20px; 
        border-left: 6px solid #4ECDC4; margin: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 2rem; justify-content: center; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border: none; color: #a0a0c0; }
    .stTabs [aria-selected="true"] { color: #ffffff; border-bottom: 3px solid #ff4b4b; }
    .issue-card {
        background-color: #2c2c54; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;
        border-left: 5px solid #ff4b4b; /* Critical */
    }
    .issue-card-critical { border-left-color: #ff4b4b; }
    .issue-card-high { border-left-color: #ff8700; }
    .issue-card-medium { border-left-color: #ffc400; }
    .issue-card-low { border-left-color: #20c997; }
</style>
""", unsafe_allow_html=True)

# --- API Configuration & Session State ---
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

for key, default in [
    ("session_id", str(uuid.uuid4())), ("analysis_results", None),
    ("chat_messages", []), ("analysis_id", None), ("analysis_status", "idle")
]:
    if key not in st.session_state: st.session_state[key] = default

def make_api_request(endpoint: str, method: str = "POST", data: Any = None, files: Any = None):
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET": 
            response = requests.get(url, timeout=20)
        else: 
            response = requests.post(url, data=data, files=files, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}", icon="🚨")
        st.session_state.analysis_status = "failed"
        return None

def display_header():
    st.markdown('<div class="main-header">CodeIQ: AI Code Intelligence</div>', unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #a0a0c0;'>Analyze, understand, and chat with your entire codebase.</h4>", unsafe_allow_html=True)
    st.divider()

def display_metric_card(title, value, score_of=10, icon=""):
    st.markdown(f"""
    <div class="metric-card">
        <p style="font-size: 1rem; color: #FAFAFA; margin: 0;">{icon} {title}</p>
        <h2 style="color: #FFFFFF; margin: 0; font-weight: bold; font-size: 2.5rem;">{value}<span style="font-size: 1.5rem; color: #A0A0A0;">/{score_of}</span></h2>
    </div>
    """, unsafe_allow_html=True)

def display_comprehensive_dashboard(results: Dict):
    st.markdown("<div class='info-box'>🎉 <strong>Analysis Complete!</strong> Here's the comprehensive report for your codebase.</div>", unsafe_allow_html=True)
    if results.get("rag_index_path"):
        st.markdown("<div class='info-box rag'>🧠 <strong>RAG Enabled:</strong> You can now ask detailed questions about the source code in the 'Interactive Chat' tab.</div>", unsafe_allow_html=True)

    scores = results.get("overall_scores", {})
    cols = st.columns(5)
    with cols[0]: display_metric_card("Overall Score", scores.get('overall', 0), icon="🏆")
    with cols[1]: display_metric_card("Security", scores.get('security', 0), icon="🛡️")
    with cols[2]: display_metric_card("Performance", scores.get('performance', 0), icon="⚡")
    with cols[3]: display_metric_card("Maintainability", scores.get('maintainability', 0), icon="🔧")
    with cols[4]: display_metric_card("Documentation", scores.get('documentation', 0), icon="📚")
    
    st.divider()
    
    # Enhanced Visualizations Section
    tab_viz, tab_issues = st.tabs(["📊 **Visualizations**", "🔍 **Detailed Findings**"])
    
    with tab_viz:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Quality Score Breakdown")
            if scores:
                categories = ['security', 'performance', 'maintainability', 'documentation', 'complexity']
                radar_df = pd.DataFrame(dict(
                    r=[scores.get(cat, 0) for cat in categories], 
                    theta=[cat.capitalize() for cat in categories]
                ))
                fig = px.line_polar(radar_df, r='r', theta='theta', line_close=True, range_r=[0, 10])
                fig.update_traces(fill='toself', line=dict(color='#4ECDC4'))
                fig.update_layout(
                    polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(gridcolor="#444")),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Language Distribution")
            if results.get("languages_detected"):
                lang_df = pd.DataFrame(results["languages_detected"].items(), columns=["Language", "Files"])
                fig = px.pie(lang_df, values="Files", names="Language", hole=.4)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

    with tab_issues:
        st.subheader("Prioritized Issue List")
        
        # --- FINAL, AI-DRIVEN ISSUE DISPLAY ---
        def display_issue_list(issue_type_key: str):
            all_issues = []
            # Extract issues from file analyses with enhanced structure
            for file_analysis in results.get('file_analyses', {}).values():
                issues = file_analysis.get(issue_type_key, [])
                for issue in issues:
                    # Ensure issue has proper structure for AI-driven display
                    enhanced_issue = {
                        'filepath': file_analysis.get('filepath', 'Unknown'),
                        'type': issue.get('type', issue.get('category', 'Issue')),
                        'severity': issue.get('severity', 'Low'),
                        'line': issue.get('line', 0),
                        'explanation': issue.get('explanation', issue.get('description', 'No explanation available')),
                        'fix_suggestion': issue.get('fix_suggestion', issue.get('suggestion', 'No fix suggestion available')),
                        'code': issue.get('code', '')
                    }
                    all_issues.append(enhanced_issue)
            
            if not all_issues:
                st.success(f"✅ No major {issue_type_key.replace('_', ' ')} issues were found by the AI agent.")
                return

            # Sort by severity
            severity_map = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
            sorted_issues = sorted(all_issues, key=lambda x: severity_map.get(x.get('severity', 'Low'), 4))

            # Display issues with enhanced AI-driven format
            for issue in sorted_issues:
                severity = issue.get('severity', 'Low').lower()
                
                with st.expander(
                    f"**{issue.get('severity', 'Low').upper()}**: {issue.get('type', 'Issue')} in `{issue['filepath']}` (Line ~{issue.get('line')})",
                    expanded=severity in ['critical', 'high']
                ):
                    st.markdown(f"<div class='issue-card issue-card-{severity}'>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.markdown(f"**Severity:** {issue.get('severity', 'Low').upper()}")
                        st.markdown(f"**File:** `{issue['filepath']}`")
                        st.markdown(f"**Line:** ~{issue.get('line')}")
                        if issue.get('code'):
                            st.markdown("**Code:**")
                            st.code(issue.get('code', ''), language='text')
                    
                    with col2:
                        st.markdown("**AI Explanation:**")
                        st.info(issue.get('explanation', 'No explanation available'))
                        
                        st.markdown("**Suggested Fix:**")
                        fix_suggestion = issue.get('fix_suggestion', 'No fix suggestion available')
                        if fix_suggestion and fix_suggestion != 'No fix suggestion available':
                            st.code(fix_suggestion, language='diff')
                        else:
                            st.warning("No specific fix suggestion available")
                    
                    st.markdown("</div>", unsafe_allow_html=True)

        # Issue type tabs
        issue_tabs = st.tabs(["🛡️ Security", "⚡ Performance", "🔧 Quality (AST)", "🏗️ Architecture", "🔬 Testing Gaps"])
        
        with issue_tabs[0]: 
            display_issue_list('security_issues')
        with issue_tabs[1]: 
            display_issue_list('performance_issues')
        with issue_tabs[2]: 
            # Quality issues from AST analysis
            quality_data = []
            for analysis in results.get('file_analyses', {}).values():
                quality_data.extend(analysis.get('quality_issues', []))
            if quality_data:
                st.dataframe(pd.DataFrame(quality_data), use_container_width=True)
            else:
                st.success("✅ No quality issues found.")
        
        with issue_tabs[3]: 
            arch_data = results.get("architecture_issues", [])
            if arch_data:
                st.dataframe(pd.DataFrame(arch_data), use_container_width=True)
            else:
                st.success("✅ No architecture issues found.")
                
        with issue_tabs[4]: 
            test_data = results.get("testing_gaps", [])
            if test_data:
                st.dataframe(pd.DataFrame(test_data), use_container_width=True)
            else:
                st.success("✅ No testing gaps identified.")

def poll_for_results():
    """Poll for analysis results when processing"""
    progress_text = f"Analysis in progress for ID: {st.session_state.analysis_id}... This can take several minutes."
    with st.spinner(progress_text):
        time.sleep(10)
        status_response = make_api_request(f"/analyze/{st.session_state.analysis_id}/status", "GET")
        if status_response and status_response.get("status") == "completed":
            st.session_state.analysis_status = "completed"
            st.session_state.analysis_results = status_response.get("results")
            st.rerun()
        elif status_response and status_response.get("status") == "failed":
            st.session_state.analysis_status = "failed"
            st.error(f"Analysis Failed: {status_response.get('error', 'Unknown error')}", icon="❌")
        else: 
            st.rerun()

def analysis_page():
    """Analysis page logic"""
    st.header("🏗️ Start a New Analysis")
    analysis_mode = st.radio("Source", ["🌐 GitHub Repository", "📤 Upload Project Files"], horizontal=True, label_visibility="collapsed")
    
    def start_new_analysis():
        st.session_state.update({
            "analysis_status": "processing", 
            "analysis_results": None, 
            "chat_messages": [], 
            "analysis_id": None
        })

    if analysis_mode == "🌐 GitHub Repository":
        github_url = st.text_input(
            "Public GitHub Repository URL", 
            placeholder="e.g., https://github.com/langchain-ai/langchain"
        )
        if st.button("🚀 Analyze Repository", type="primary", disabled=not github_url):
            start_new_analysis()
            response = make_api_request("/analyze/comprehensive", data={"github_url": github_url})
            if response: 
                st.session_state.analysis_id = response.get("analysis_id")
            st.rerun()
    else:
        uploaded_files = st.file_uploader(
            "Upload all files from your project folder", 
            accept_multiple_files=True
        )
        if st.button("🚀 Analyze Uploaded Files", type="primary", disabled=not uploaded_files):
            start_new_analysis()
            files = [("files", (f.name, f.getvalue())) for f in uploaded_files]
            response = make_api_request("/analyze/comprehensive", files=files)
            if response: 
                st.session_state.analysis_id = response.get("analysis_id")
            st.rerun()

def chat_page():
    """Chat page logic"""
    st.header("💬 Interactive Chat")
    if st.session_state.analysis_status != "completed":
        st.info("⚠️ Please complete an analysis on the 'Analysis & Dashboard' tab to enable the chat.", icon="ℹ️")
    else:
        st.markdown(f"<div class='info-box'>🎯 <strong>Context Loaded:</strong> Analysis ID <code>{st.session_state.analysis_id}</code></div>", unsafe_allow_html=True)
        chat_mode = st.radio("Chat Mode:", ["Report Summary Q&A", "Ask the Codebase (RAG)"], horizontal=True)
        
        # Display chat history
        for msg in st.session_state.chat_messages:
            avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
                if "sources" in msg and msg["sources"]:
                    st.caption("Retrieved from: " + ", ".join(msg["sources"]))
        
        # Chat input
        if prompt := st.chat_input("Ask a question..."):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            st.chat_message("user", avatar="🧑‍💻").write(prompt)
            
            endpoint = "/chat/rag_query" if chat_mode == "Ask the Codebase (RAG)" else "/chat/summary_query"
            payload = {
                "query": prompt, 
                "session_id": st.session_state.session_id, 
                "analysis_id": st.session_state.analysis_id
            }

            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking..."):
                    response = make_api_request(endpoint, data=json.dumps(payload))
                    if response and response.get("status") == "success":
                        answer = response["response"]["answer"]
                        sources = response["response"].get("sources")
                        st.markdown(answer)
                        if sources: 
                            st.caption("Retrieved from: " + ", ".join(sources))
                        st.session_state.chat_messages.append({
                            "role": "assistant", 
                            "content": answer, 
                            "sources": sources
                        })
                    else:
                        error_msg = response.get("error", "Sorry, I couldn't get a response.") if response else "Sorry, I couldn't get a response."
                        st.error(error_msg)
                        st.session_state.chat_messages.append({
                            "role": "assistant", 
                            "content": error_msg
                        })

def main():
    display_header()
    tab1, tab2 = st.tabs(["🔬 **Analysis & Dashboard**", "💬 **Interactive Chat**"])

    with tab1:
        analysis_page()
        st.divider()
        
        if st.session_state.analysis_status == "processing": 
            poll_for_results()
        elif st.session_state.analysis_status == "completed" and st.session_state.analysis_results: 
            display_comprehensive_dashboard(st.session_state.analysis_results)
            
    with tab2:
        chat_page()

if __name__ == "__main__":
    main()