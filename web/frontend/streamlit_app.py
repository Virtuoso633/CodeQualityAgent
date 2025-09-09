"""
Streamlit Frontend for Code Quality Intelligence Agent - FINAL POLISHED VERSION
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
st.set_page_config(
    page_title="CodeIQ 🤖",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
st.markdown("""
<style>
    /* Main Header */
    .main-header {
        font-size: 3rem; font-weight: bold; text-align: center; margin-bottom: 2rem;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    /* Custom info/success boxes */
    .custom-info-box {
        background-color: #262730; border-radius: 10px; padding: 15px;
        border-left: 5px solid #4ECDC4; margin-bottom: 1rem;
    }
    /* Make chat bubbles more distinct */
    .st-emotion-cache-1f1G22h { /* Assistant message */
        background-color: #2a3949;
    }
</style>
""", unsafe_allow_html=True)

# --- API Configuration & Session State ---
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

# Initialize session state keys
for key, default in [
    ("session_id", str(uuid.uuid4())), ("analysis_results", None),
    ("chat_messages", []), ("analysis_id", None),
    ("analysis_status", "idle") # States: idle, processing, completed, failed
]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- API Helper ---
def make_api_request(endpoint: str, method: str = "POST", data: Any = None, files: Any = None):
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, data=data, files=files, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}", icon="🚨")
        st.session_state.analysis_status = "failed"
        return None

# --- UI Display Components ---
def display_header():
    st.markdown('<div class="main-header">CodeIQ: AI Code Intelligence</div>', unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center;'>Analyze massive codebases and ask questions directly to your code with RAG.</h4>", unsafe_allow_html=True)
    st.divider()

def display_metric_card(title, value, score_of=10, icon=""):
    st.markdown(f"""
    <div style="background-color: #262730; border-radius: 10px; padding: 20px; border-left: 6px solid #4ECDC4;">
        <p style="font-size: 1rem; color: #FAFAFA; margin: 0;">{icon} {title}</p>
        <h2 style="color: #FFFFFF; margin: 0; font-weight: bold; font-size: 2.5rem;">{value}<span style="font-size: 1.5rem; color: #A0A0A0;">/{score_of}</span></h2>
    </div>
    """, unsafe_allow_html=True)

def display_comprehensive_dashboard(results: Dict):
    st.markdown("<div class='custom-info-box'>🎉 <strong>Analysis Complete!</strong> Here's the comprehensive report for your codebase.</div>", unsafe_allow_html=True)

    scores = results.get("overall_scores", {})
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: display_metric_card("Overall Score", scores.get('overall', 0), icon="🏆")
    with col2: display_metric_card("Security", scores.get('security', 0), icon="🛡️")
    with col3: display_metric_card("Performance", scores.get('performance', 0), icon="⚡")
    with col4: display_metric_card("Maintainability", scores.get('maintainability', 0), icon="🔧")
    with col5: display_metric_card("Documentation", scores.get('documentation', 0), icon="📚")

    st.divider()

    viz_col, lang_col = st.columns([2, 1])
    with viz_col:
        st.subheader("📊 Quality Score Breakdown")
        if scores:
            categories = ['security', 'performance', 'maintainability', 'documentation', 'complexity']
            radar_df = pd.DataFrame(dict(r=[scores.get(cat, 0) for cat in categories], theta=[cat.capitalize() for cat in categories]))
            fig = px.line_polar(radar_df, r='r', theta='theta', line_close=True, range_r=[0, 10], title="Code Quality Radar")
            fig.update_traces(fill='toself', line=dict(color='#4ECDC4'))
            st.plotly_chart(fig, use_container_width=True)

    with lang_col:
        st.subheader("🔤 Language Distribution")
        if results.get("languages_detected"):
            lang_df = pd.DataFrame(results["languages_detected"].items(), columns=["Language", "Files"])
            fig = px.pie(lang_df, values="Files", names="Language", title="Files by Language", hole=.4)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("🔍 Detailed Findings")
    # ... Add tabs and dataframes for detailed issues as before ...

# --- Page Logic Functions ---
def analysis_page():
    st.header("🏗️ Start a New Analysis")
    st.markdown("Analyze an entire repository from a public GitHub URL or by uploading your project files.")

    analysis_mode = st.radio("Choose Analysis Source", ["🌐 GitHub Repository", "📤 Upload Project Files"], horizontal=True, label_visibility="collapsed")
    
    # Reset state if starting a new analysis
    def start_new_analysis():
        st.session_state.analysis_status = "processing"
        st.session_state.analysis_results = None
        st.session_state.chat_messages = []

    if analysis_mode == "🌐 GitHub Repository":
        github_url = st.text_input("Public GitHub Repository URL", placeholder="e.g., https://github.com/langchain-ai/langchain")
        if st.button("🚀 Analyze Repository", type="primary", disabled=not github_url):
            start_new_analysis()
            response = make_api_request("/analyze/comprehensive", data={"github_url": github_url})
            if response: st.session_state.analysis_id = response.get("analysis_id")
            st.rerun()

    else: # Upload Project Files
        uploaded_files = st.file_uploader("Upload all files from your project folder", accept_multiple_files=True)
        if st.button("🚀 Analyze Uploaded Files", type="primary", disabled=not uploaded_files):
            start_new_analysis()
            files_for_upload = [("files", (file.name, file.getvalue())) for file in uploaded_files]
            response = make_api_request("/analyze/comprehensive", files=files_for_upload)
            if response: st.session_state.analysis_id = response.get("analysis_id")
            st.rerun()

def poll_for_results():
    if st.session_state.analysis_status == "processing":
        progress_text = f"Analysis in progress for ID: {st.session_state.analysis_id}... This may take several minutes."
        with st.spinner(progress_text):
            time.sleep(10)
            status_response = make_api_request(f"/analyze/{st.session_state.analysis_id}/status", "GET")
            if status_response:
                if status_response.get("status") == "completed":
                    st.session_state.analysis_status = "completed"
                    st.session_state.analysis_results = status_response.get("results")
                    st.rerun()
                elif status_response.get("status") == "failed":
                    st.session_state.analysis_status = "failed"
                    st.error(f"Analysis Failed: {status_response.get('error', 'Unknown error')}", icon="❌")
                else: # Still processing
                    st.rerun()

def chat_page():
    st.header("💬 Interactive Chat")
    if st.session_state.analysis_status != "completed":
        st.info("⚠️ Please complete a codebase analysis on the 'Analysis' page to enable the chat.", icon="ℹ️")
        return

    st.markdown(f"<div class='custom-info-box'>🎯 <strong>Context Loaded:</strong> Analysis ID <code>{st.session_state.analysis_id}</code></div>", unsafe_allow_html=True)
    
    chat_mode = st.radio(
        "Select Chat Mode:",
        ["**Chat with Analysis Report** (For summaries & scores)", "**Ask the Codebase (RAG)** (For specific code questions)"],
        horizontal=True
    )

    # Display chat history
    for msg in st.session_state.chat_messages:
        avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if "sources" in msg and msg["sources"]:
                st.caption("Retrieved from: " + ", ".join(msg["sources"]))

    if prompt := st.chat_input("Ask a question about your code..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        st.chat_message("user", avatar="🧑‍💻").write(prompt)

        endpoint = "/chat/rag_query" if "RAG" in chat_mode else "/chat/summary_query"
        payload = {"query": prompt, "session_id": st.session_state.session_id, "analysis_id": st.session_state.analysis_id}

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                response = make_api_request(endpoint, data=json.dumps(payload))
                if response and response.get("status") == "success":
                    answer = response["response"]["answer"]
                    sources = response["response"].get("sources")
                    st.markdown(answer)
                    if sources:
                        st.caption("Retrieved from: " + ", ".join(sources))
                    st.session_state.chat_messages.append({"role": "assistant", "content": answer, "sources": sources})
                else:
                    error_msg = response.get("error", "Sorry, I couldn't get a response.") if response else "Sorry, I couldn't get a response."
                    st.error(error_msg)
                    st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})

# --- Main Application Layout ---
def main():
    display_header()
    
    # Using tabs for the main navigation
    tab1, tab2 = st.tabs(["🔬 Analysis & Dashboard", "💬 Interactive Chat"])

    with tab1:
        analysis_page()
        if st.session_state.analysis_status == "processing":
            poll_for_results()
        elif st.session_state.analysis_status == "completed" and st.session_state.analysis_results:
            display_comprehensive_dashboard(st.session_state.analysis_results)
    
    with tab2:
        chat_page()

if __name__ == "__main__":
    main()