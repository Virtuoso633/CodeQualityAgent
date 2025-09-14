"""
Streamlit Frontend for Code Quality Intelligence Agent - V8 (Using mermaid.live link)
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json
import time
import uuid
import os
import base64
import zlib

# --- Page Configuration ---
st.set_page_config(page_title="CodeIQ 🤖", page_icon="🤖", layout="wide")

# --- MERMAID.LIVE LINK GENERATION (Your excellent code) ---
def js_btoa(data):
    return base64.b64encode(data)

def pako_deflate(data):
    compress = zlib.compressobj(9, zlib.DEFLATED, 15, 8, zlib.Z_DEFAULT_STRATEGY)
    compressed_data = compress.compress(data)
    compressed_data += compress.flush()
    return compressed_data

def genPakoLink(graphMarkdown: str):
    jGraph = {"code": graphMarkdown, "mermaid": {"theme": "default"}}
    byteStr = json.dumps(jGraph).encode('utf-8')
    deflated = pako_deflate(byteStr)
    dEncode = js_btoa(deflated)
    link = 'https://mermaid.live/edit#pako:' + dEncode.decode('ascii')
    return link

# --- API Configuration & Session State ---
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

for key, default in [
    ("session_id", str(uuid.uuid4())), ("analysis_results", None),
    ("chat_messages", []), ("analysis_id", None), ("analysis_status", "idle")
]:
    if key not in st.session_state: st.session_state[key] = default

# --- STYLING ---
st.markdown("""
<style>
    /* Core Layout & Bug Fixes */
    .stApp { display: flex; flex-direction: column; min-height: 100vh; }
    .stApp > div:first-child > div:first-child > div:first-child { flex-grow: 1; }
    /* General Styling */
    body { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0E1117; }
    h1, h2, h3 { color: #FAFAFA; }
    .main-header {
        font-size: 2.5rem; font-weight: bold; text-align: center; margin-bottom: 1rem;
        background: linear-gradient(90deg, #4ECDC4, #45B7D1);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    /* Component Styling */
    [data-testid="stSidebar"] { background-color: #1A1F2B; }
    [data-testid="stSidebar"] h2 { font-size: 1.5rem; color: #FAFAFA; }
    .metric-card {
        background-color: #1A1F2B; border-radius: 10px; padding: 1.5rem;
        border-left: 5px solid #4ECDC4; margin: 0.5rem 0;
        transition: all 0.2s ease-in-out;
    }
    .metric-card:hover { transform: translateY(-5px); box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2); }
    .metric-card p { font-size: 1rem; color: #A0AEC0; margin: 0; }
    .metric-card h2 { color: #FFFFFF; margin: 0; font-weight: bold; font-size: 2.5rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 1.5rem; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border: none; color: #A0AEC0; }
    .stTabs [aria-selected="true"] { color: #FFFFFF; border-bottom: 3px solid #4ECDC4; }
    .stExpander { border: 1px solid #2D3748; border-radius: 8px; }
    /* Chat Interface Styling */
    .stChatMessage { border-radius: 10px; padding: 1rem; margin-bottom: 1rem; }
    .stChatMessage[data-testid="chat-message-container-assistant"] { background-color: #2D3748; }
</style>
""", unsafe_allow_html=True)

# --- API HELPER ---
def make_api_request(endpoint: str, method: str = "POST", data: any = None, files: any = None):
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.request(method, url, data=data, files=files, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}", icon="🚨")
        st.session_state.analysis_status = "failed"
        return None

# --- UI COMPONENTS ---
def display_sidebar():
    with st.sidebar:
        st.header("CodeIQ 🤖")
        st.subheader("Start New Analysis")
        analysis_mode = st.radio("Source", ["🌐 GitHub Repository", "📤 Upload Project Files"], label_visibility="collapsed")

        def start_new_analysis():
            st.session_state.update({"analysis_status": "processing", "analysis_results": None, "chat_messages": [], "analysis_id": None})

        if analysis_mode == "🌐 GitHub Repository":
            github_url = st.text_input("Public or Private GitHub URL", placeholder="https://github.com/user/repo")
            if st.button("🚀 Analyze Repository", type="primary", use_container_width=True, disabled=not github_url):
                start_new_analysis()
                response = make_api_request("/analyze/comprehensive", data={"github_url": github_url})
                if response: st.session_state.analysis_id = response.get("analysis_id")
                st.rerun()
        else:
            uploaded_files = st.file_uploader("Upload project files", accept_multiple_files=True)
            if st.button("🚀 Analyze Uploaded Files", type="primary", use_container_width=True, disabled=not uploaded_files):
                start_new_analysis()
                files = [("files", (f.name, f.getvalue())) for f in uploaded_files]
                response = make_api_request("/analyze/comprehensive", files=files)
                if response: st.session_state.analysis_id = response.get("analysis_id")
                st.rerun()
        st.info("For private repos, ensure `GITHUB_TOKEN` is set in your `.env` file.")

def display_metric_card(title, value, score_of=10, icon=""):
    st.markdown(f"""<div class="metric-card"><p>{icon} {title}</p><h2>{value}<span style="font-size: 1.5rem; color: #A0AEC0;">/{score_of}</span></h2></div>""", unsafe_allow_html=True)

def display_issue_tabs(results: dict):
    sec_tab, perf_tab, quality_tab, arch_tab, test_tab = st.tabs([
        "🛡️ Security", "⚡ Performance", "🔧 Quality (AST)", "🏗️ Architecture", "🔬 Testing Gaps"
    ])

    def display_issue_list(issue_type_key: str):
        all_issues = [ {**issue, 'filepath': file.get('filepath', 'Unknown')} for file in results.get('file_analyses', {}).values() for issue in file.get(issue_type_key, []) ]
        if not all_issues:
            st.success(f"✅ No major {issue_type_key.replace('_', ' ')} issues were found.")
            return
        severity_map = {"Critical":0, "High": 1, "Medium": 2, "Low": 3}
        sorted_issues = sorted(all_issues, key=lambda x: severity_map.get(x.get('severity', 'Low'), 4))
        for issue in sorted_issues:
            with st.expander(f"**{issue.get('severity', 'Low').upper()}**: {issue.get('type', 'Issue')} in `{issue['filepath']}`"):
                st.markdown(f"**Line:** `~{issue.get('line', 'N/A')}`")
                st.markdown("**AI Explanation:**"); st.warning(issue.get('explanation', 'No explanation available.'))
                st.markdown("**Suggested Fix:**"); st.code(issue.get('fix_suggestion', 'No specific fix suggestion available.'), language='diff')

    with sec_tab: display_issue_list('security_issues')
    with perf_tab: display_issue_list('performance_issues')
    with quality_tab:
        quality_issues = [ {**issue, 'filepath': file.get('filepath', 'Unknown')} for file in results.get('file_analyses', {}).values() for issue in file.get('quality_issues', []) ]
        if not quality_issues: st.success("✅ No AST quality issues found.")
        else: st.dataframe(pd.DataFrame(quality_issues), use_container_width=True)
    
    with arch_tab:
        st.subheader("AI-Generated Architecture Diagram")
        mermaid_code = results.get("architecture_summary", "graph TD\n    A[Error] --> B[No summary received from backend]")
        
        st.markdown("#### Raw Mermaid Code Received from Backend")
        st.code(mermaid_code, language='markdown')

        if mermaid_code and mermaid_code.strip().startswith("graph"):
            mermaid_link = genPakoLink(mermaid_code)
            st.link_button("🔗 Open and Edit Diagram in Live Editor", mermaid_link, use_container_width=True)
        else:
            st.error("The AI failed to generate a valid Mermaid diagram. The raw output is shown above.")

    with test_tab:
        gaps = results.get("testing_gaps", [])
        if not gaps: st.success("✅ No major testing gaps identified.")
        else: st.dataframe(pd.DataFrame(gaps), use_container_width=True)

def display_dashboard(results: dict):
    st.markdown('<div class="main-header">Analysis Dashboard</div>', unsafe_allow_html=True)
    scores = results.get("overall_scores", {})
    cols = st.columns(5)
    with cols[0]: display_metric_card("Overall Score", scores.get('overall', 0), icon="🏆")
    with cols[1]: display_metric_card("Security", scores.get('security', 0), icon="🛡️")
    with cols[2]: display_metric_card("Performance", scores.get('performance', 0), icon="⚡")
    with cols[3]: display_metric_card("Maintainability", scores.get('maintainability', 0), icon="🔧")
    with cols[4]: display_metric_card("Documentation", scores.get('documentation', 0), icon="📚")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Executive Summary")
    st.info(results.get("crew_ai_summary", "AI summary could not be generated."))

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Codebase Visualizations")
    vis_col1, vis_col2 = st.columns(2)
    with vis_col1:
        st.markdown("###### Score Breakdown")
        categories = ['security', 'performance', 'maintainability', 'documentation']
        radar_df = pd.DataFrame(dict(r=[scores.get(cat, 0) for cat in categories], theta=[cat.capitalize() for cat in categories]))
        fig_radar = px.line_polar(radar_df, r='r', theta='theta', line_close=True)
        fig_radar.update_traces(fill='toself', line=dict(color='#4ECDC4'))
        fig_radar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#FAFAFA")
        st.plotly_chart(fig_radar, use_container_width=True)
    
    with vis_col2:
        st.markdown("###### Language Distribution")
        if results.get("languages_detected"):
            lang_df = pd.DataFrame(results["languages_detected"].items(), columns=["Language", "Files"])
            fig_pie = px.pie(lang_df, values="Files", names="Language", hole=.4, color_discrete_sequence=px.colors.sequential.Cividis_r)
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend_font_color="#FAFAFA")
            st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Detailed Findings")
    display_issue_tabs(results)

def display_chat_interface():
    st.markdown('<div class="main-header">Interactive Chat</div>', unsafe_allow_html=True)
    if st.session_state.analysis_status != "completed":
        st.info("Please complete an analysis to enable the chat.", icon="ℹ️"); return

    st.info(f"**Context Loaded:** You are now chatting about Analysis ID `{st.session_state.analysis_id}`.")
    chat_mode = st.radio("Chat Mode:", ["Report Summary Q&A", "Ask the Codebase (RAG)"], horizontal=True)
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sources" in msg and msg["sources"]: st.caption("Sources: " + ", ".join(f"`{s}`" for s in msg["sources"]))

    if prompt := st.chat_input("Ask a question..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        endpoint = "/chat/rag_query" if chat_mode == "Ask the Codebase (RAG)" else "/chat/summary_query"
        payload = {"query": prompt, "session_id": st.session_state.session_id, "analysis_id": st.session_state.analysis_id}
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = make_api_request(endpoint, data=json.dumps(payload))
                if response and response.get("status") == "success":
                    answer = response["response"]["answer"]
                    sources = response["response"].get("sources")
                    st.session_state.chat_messages.append({"role": "assistant", "content": answer, "sources": sources})
                else:
                    st.session_state.chat_messages.append({"role": "assistant", "content": "Sorry, I couldn't get a response."})
        st.rerun()

def main():
    display_sidebar()
    if st.session_state.analysis_status == "idle":
        st.markdown('<div class="main-header">Welcome to CodeIQ</div>', unsafe_allow_html=True)
        st.info("⬅️ Start a new analysis using the sidebar to begin.")
    elif st.session_state.analysis_status == "processing":
        with st.spinner(f"Analysis in progress... This can take a few minutes."):
            time.sleep(10)
            status_response = make_api_request(f"/analyze/{st.session_state.analysis_id}/status", "GET")
            if status_response:
                if status_response.get("status") == "completed":
                    st.session_state.analysis_status = "completed"; st.session_state.analysis_results = status_response.get("results"); st.rerun()
                elif status_response.get("status") == "failed":
                    st.session_state.analysis_status = "failed"; st.error(f"Analysis Failed: {status_response.get('error', 'Unknown error')}", icon="❌")
                else: st.rerun()
    elif st.session_state.analysis_status == "completed" and st.session_state.analysis_results:
        tab1, tab2 = st.tabs(["🔬 Dashboard", "💬 Chat"])
        with tab1: display_dashboard(st.session_state.analysis_results)
        with tab2: display_chat_interface()
    elif st.session_state.analysis_status == "failed":
        st.error("The last analysis failed. Please try again from the sidebar.")

if __name__ == "__main__":
    main()