"""
Codebase Genius - Streamlit Frontend
Professional web interface for the documentation generation system

Features:
- Clean, modern UI design
- Real-time progress tracking
- Documentation preview
- Error handling and user feedback
- Multiple repository support
- Export and download capabilities
"""

import streamlit as st
import requests
import json
import os
from pathlib import Path
from datetime import datetime
import time

# Configuration
JAC_SERVER_URL = os.getenv("JAC_SERVER_URL", "http://localhost:8000")
DEFAULT_OUTPUT_DIR = "./outputs"

# Page configuration
st.set_page_config(
    page_title="Codebase Genius",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        font-size: 3.5rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        padding: 1rem 0;
    }
    
    .sub-header {
        font-size: 1.3rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    
    /* Success message box */
    .success-box {
        padding: 1.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .success-box strong {
        color: #fff;
    }
    
    /* Error message box */
    .error-box {
        padding: 1.5rem;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Info box */
    .info-box {
        padding: 1rem;
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    /* Warning box */
    .warning-box {
        padding: 1rem;
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Card styling */
    .card {
        padding: 1.5rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Metric styling */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'generation_history' not in st.session_state:
    st.session_state.generation_history = []

if 'current_status' not in st.session_state:
    st.session_state.current_status = None

# Header
st.markdown('<div class="main-header">🧠 Codebase Genius</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Automatic Code Documentation Generator</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Output directory
    output_dir = st.text_input(
        "Output Directory",
        value=DEFAULT_OUTPUT_DIR,
        help="Directory where documentation will be saved"
    )
    
    # Server URL
    server_url = st.text_input(
        "Jac Server URL",
        value=JAC_SERVER_URL,
        help="URL of the running Jac server"
    )
    
    st.markdown("---")
    
    # Server status check
    st.subheader("🔌 Server Status")
    
    def check_server_status():
        try:
            response = requests.get(f"{server_url}/docs", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    if st.button("Check Connection", use_container_width=True):
        with st.spinner("Checking..."):
            if check_server_status():
                st.success("✅ Server Online")
            else:
                st.error("❌ Server Offline")
                st.info("Make sure to run: `jac serve main.jac`")
    
    st.markdown("---")
    
    # Statistics
    st.subheader("📊 Statistics")
    st.metric("Total Generations", len(st.session_state.generation_history))
    
    if st.session_state.generation_history:
        successful = sum(1 for g in st.session_state.generation_history if g.get('status') == 'completed')
        st.metric("Successful", successful)
        st.metric("Success Rate", f"{(successful/len(st.session_state.generation_history)*100):.1f}%")
    
    st.markdown("---")
    
    # About section
    st.subheader("📖 About")
    st.markdown("""
    **Codebase Genius** automatically generates comprehensive documentation for your code repositories.
    
    **Features:**
    - 🗺️ Repository mapping
    - 🔍 Deep code analysis
    - 📝 Markdown generation
    - 📊 Architecture diagrams
    - 🐍 Python & Jac support
    
    **Version:** 1.0.0
    """)
    
    st.markdown("---")
    
    # Clear history button
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.generation_history = []
        st.rerun()

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Generate Docs", "📚 View Docs", "📜 History", "❓ Help"])

with tab1:
    st.header("Generate Documentation")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        github_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/username/repository",
            help="Enter a public GitHub repository URL"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        generate_btn = st.button("🚀 Generate", type="primary", use_container_width=True)
    
    # Advanced options (collapsible)
    with st.expander("⚙️ Advanced Options"):
        col_a, col_b = st.columns(2)
        
        with col_a:
            include_diagrams = st.checkbox("Include Diagrams", value=True)
            analyze_complexity = st.checkbox("Analyze Complexity", value=True)
        
        with col_b:
            max_files = st.number_input("Max Files to Analyze", min_value=10, max_value=200, value=50)
            timeout = st.number_input("Timeout (seconds)", min_value=60, max_value=600, value=300)
    
    if generate_btn:
        if not github_url:
            st.error("❌ Please enter a GitHub URL")
        elif not github_url.startswith("http"):
            st.error("❌ Please enter a valid URL starting with http:// or https://")
        else:
            # Create progress container
            progress_container = st.container()
            
            with progress_container:
                st.markdown("### 🔄 Generation Progress")
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Status updates
                status_text.text("⏳ Initializing...")
                progress_bar.progress(10)
                
                try:
                    start_time = time.time()
                    
                    # Call the Jac server
                    status_text.text("🌐 Connecting to Jac server...")
                    progress_bar.progress(20)
                    
                    response = requests.post(
                        f"{server_url}/walker/DocumentRepository",
                        json={
                            "github_url": github_url,
                            "output_dir": output_dir
                        },
                        timeout=timeout
                    )
                    
                    progress_bar.progress(40)
                    status_text.text("🗺️ Mapping repository structure...")
                    time.sleep(0.5)
                    
                    progress_bar.progress(60)
                    status_text.text("🔍 Analyzing code...")
                    time.sleep(0.5)
                    
                    progress_bar.progress(80)
                    status_text.text("📝 Generating documentation...")
                    time.sleep(0.5)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Complete!")
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result.get("status") == "completed":
                            # Success!
                            st.balloons()
                            
                            st.markdown(f"""
                            <div class="success-box">
                                <h3>✅ Documentation Generated Successfully!</h3>
                                <p><strong>Repository:</strong> {result.get('repository', 'Unknown')}</p>
                                <p><strong>Output Path:</strong> <code>{result.get('output_path', 'Unknown')}</code></p>
                                <p><strong>Time Taken:</strong> {duration:.1f} seconds</p>
                                <p><strong>Timestamp:</strong> {result.get('timestamp', 'Unknown')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Add to history
                            st.session_state.generation_history.append({
                                'url': github_url,
                                'status': 'completed',
                                'timestamp': datetime.now().isoformat(),
                                'duration': duration,
                                'output_path': result.get('output_path')
                            })
                            
                            # Try to load and display the documentation
                            output_path = result.get('output_path')
                            if output_path and os.path.exists(output_path):
                                with st.expander("📄 Preview Generated Documentation", expanded=True):
                                    with open(output_path, 'r', encoding='utf-8') as f:
                                        doc_content = f.read()
                                    
                                    # Show first 2000 characters
                                    preview_length = 2000
                                    if len(doc_content) > preview_length:
                                        st.markdown(doc_content[:preview_length] + "\n\n*... [Preview truncated. Download full documentation below]*")
                                    else:
                                        st.markdown(doc_content)
                                    
                                    # Download button
                                    st.download_button(
                                        label="📥 Download Full Documentation",
                                        data=doc_content,
                                        file_name=f"{result.get('repository', 'docs')}_documentation.md",
                                        mime="text/markdown",
                                        use_container_width=True
                                    )
                            
                            # Quick actions
                            st.markdown("### 🎯 Quick Actions")
                            col_action1, col_action2, col_action3 = st.columns(3)
                            
                            with col_action1:
                                if st.button("📚 View in Docs Tab", use_container_width=True):
                                    st.session_state.active_tab = "View Docs"
                                    st.rerun()
                            
                            with col_action2:
                                if st.button("🔄 Generate Another", use_container_width=True):
                                    st.rerun()
                            
                            with col_action3:
                                if output_path and os.path.exists(output_path):
                                    if st.button("📂 Open Folder", use_container_width=True):
                                        folder = os.path.dirname(output_path)
                                        st.info(f"📂 Documentation folder: {folder}")
                        
                        else:
                            st.markdown(f"""
                            <div class="error-box">
                                <h3>❌ Generation Failed</h3>
                                <p>{result.get('message', 'Unknown error occurred')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Add to history
                            st.session_state.generation_history.append({
                                'url': github_url,
                                'status': 'failed',
                                'timestamp': datetime.now().isoformat(),
                                'error': result.get('message', 'Unknown error')
                            })
                    
                    else:
                        st.markdown(f"""
                        <div class="error-box">
                            <h3>❌ Server Error ({response.status_code})</h3>
                            <p>The server returned an error. Please check the logs.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander("🔍 Error Details"):
                            st.code(response.text)
                        
                        # Add to history
                        st.session_state.generation_history.append({
                            'url': github_url,
                            'status': 'error',
                            'timestamp': datetime.now().isoformat(),
                            'error': f"Server error {response.status_code}"
                        })
                
                except requests.exceptions.ConnectionError:
                    st.markdown("""
                    <div class="error-box">
                        <h3>❌ Connection Error</h3>
                        <p>Cannot connect to Jac server. Please ensure it's running.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.info(f"""
                    **How to start the server:**
```bash
                    jac serve main.jac
```
                    
                    Server should be running on: {server_url}
                    """)
                    
                    # Add to history
                    st.session_state.generation_history.append({
                        'url': github_url,
                        'status': 'error',
                        'timestamp': datetime.now().isoformat(),
                        'error': 'Connection error - server not running'
                    })
                
                except requests.exceptions.Timeout:
                    st.markdown("""
                    <div class="error-box">
                        <h3>⏱️ Request Timeout</h3>
                        <p>The request took too long. The repository might be too large.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.info("""
                    **Suggestions:**
                    - Try with a smaller repository (< 50 files)
                    - Increase the timeout value in Advanced Options
                    - Check your internet connection
                    """)
                    
                    # Add to history
                    st.session_state.generation_history.append({
                        'url': github_url,
                        'status': 'timeout',
                        'timestamp': datetime.now().isoformat(),
                        'error': 'Request timeout'
                    })
                
                except Exception as e:
                    st.markdown(f"""
                    <div class="error-box">
                        <h3>❌ Unexpected Error</h3>
                        <p>{str(e)}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("🔍 Full Error Details"):
                        st.exception(e)
                    
                    # Add to history
                    st.session_state.generation_history.append({
                        'url': github_url,
                        'status': 'error',
                        'timestamp': datetime.now().isoformat(),
                        'error': str(e)
                    })
    
    st.markdown("---")
    
    # Example repositories section
    st.subheader("📝 Try These Example Repositories")
    
    examples = [
        {
            "name": "Simple Python Module",
            "url": "https://github.com/navdeep-G/samplemod",
            "description": "A simple Python package - perfect for testing",
            "size": "Small (~10 files)"
        },
        {
            "name": "Flask Microframework",
            "url": "https://github.com/pallets/flask",
            "description": "Popular Python web framework",
            "size": "Large (~100+ files)"
        },
        {
            "name": "Requests Library",
            "url": "https://github.com/psf/requests",
            "description": "HTTP library for Python",
            "size": "Medium (~30 files)"
        }
    ]
    
    col_ex1, col_ex2, col_ex3 = st.columns(3)
    
    for i, (col, example) in enumerate(zip([col_ex1, col_ex2, col_ex3], examples)):
        with col:
            with st.container():
                st.markdown(f"**{example['name']}**")
                st.caption(example['description'])
                st.caption(f"📦 {example['size']}")
                
                if st.button(f"Try This →", key=f"example_{i}", use_container_width=True):
                    st.session_state.example_url = example['url']
                    st.rerun()
    
    # If an example was selected, populate the input
    if 'example_url' in st.session_state:
        st.info(f"📝 Example URL loaded: {st.session_state.example_url}")
        st.markdown("*Scroll up and click **Generate** to start*")

with tab2:
    st.header("View Generated Documentation")
    
    # List available documentation
    output_path = Path(output_dir)
    
    if output_path.exists():
        repos = [d for d in output_path.iterdir() if d.is_dir()]
        
        if repos:
            # Sort by modification time (newest first)
            repos.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Repository selector
            col_select, col_refresh = st.columns([4, 1])
            
            with col_select:
                selected_repo = st.selectbox(
                    "Select Repository",
                    options=[r.name for r in repos],
                    help="Choose a repository to view its documentation"
                )
            
            with col_refresh:
                st.write("")
                st.write("")
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()
            
            if selected_repo:
                doc_file = output_path / selected_repo / "docs.md"
                
                if doc_file.exists():
                    # File info
                    file_stats = doc_file.stat()
                    file_size = file_stats.st_size
                    mod_time = datetime.fromtimestamp(file_stats.st_mtime)
                    
                    col_info1, col_info2, col_info3 = st.columns(3)
                    
                    with col_info1:
                        st.metric("📄 File Size", f"{file_size / 1024:.1f} KB")
                    with col_info2:
                        st.metric("🕐 Last Modified", mod_time.strftime("%Y-%m-%d"))
                    with col_info3:
                        st.metric("⏰ Time", mod_time.strftime("%H:%M:%S"))
                    
                    st.markdown("---")
                    
                    # Read and display documentation
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        doc_content = f.read()
                    
                    # Action buttons
                    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
                    
                    with col_btn1:
                        st.download_button(
                            label="📥 Download",
                            data=doc_content,
                            file_name=f"{selected_repo}_docs.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    
                    with col_btn2:
                        if st.button("📋 Copy Path", use_container_width=True):
                            st.code(str(doc_file))
                    
                    with col_btn3:
                        if st.button("🔍 Raw View", use_container_width=True):
                            st.session_state.raw_view = not st.session_state.get('raw_view', False)
                    
                    with col_btn4:
                        if st.button("🗑️ Delete", use_container_width=True, type="secondary"):
                            if st.session_state.get('confirm_delete'):
                                try:
                                    doc_file.unlink()
                                    st.success("✅ Deleted successfully!")
                                    st.session_state.confirm_delete = False
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting: {e}")
                            else:
                                st.session_state.confirm_delete = True
                                st.warning("⚠️ Click again to confirm deletion")
                    
                    st.markdown("---")
                    
                    # Display documentation
                    if st.session_state.get('raw_view', False):
                        st.text_area("Raw Markdown", doc_content, height=600)
                    else:
                        st.markdown(doc_content)
                
                else:
                    st.warning("⚠️ Documentation file not found")
                    st.info(f"Expected location: {doc_file}")
        
        else:
            st.info("📭 No documentation generated yet")
            st.markdown("""
            **Get started:**
            1. Go to the **Generate Docs** tab
            2. Enter a GitHub repository URL
            3. Click **Generate**
            """)
    
    else:
        st.info("📁 Output directory does not exist yet")
        st.markdown(f"Documentation will be saved to: `{output_dir}`")

with tab3:
    st.header("Generation History")
    
    if st.session_state.generation_history:
        # Statistics
        total = len(st.session_state.generation_history)
        completed = sum(1 for h in st.session_state.generation_history if h['status'] == 'completed')
        failed = sum(1 for h in st.session_state.generation_history if h['status'] in ['failed', 'error', 'timeout'])
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            st.markdown(f"""
            <div class="metric-card">
                <h2>{total}</h2>
                <p>Total Attempts</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_stat2:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
                <h2>{completed}</h2>
                <p>Successful</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_stat3:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);">
                <h2>{failed}</h2>
                <p>Failed</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Filter options
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            filter_status = st.multiselect(
                "Filter by Status",
                options=['completed', 'failed', 'error', 'timeout'],
                default=['completed', 'failed', 'error', 'timeout']
            )
        
        with col_filter2:
            sort_order = st.selectbox(
                "Sort by",
                options=['Newest First', 'Oldest First', 'Duration (Longest)', 'Duration (Shortest)']
            )
        
        # Filter and sort
        filtered_history = [h for h in st.session_state.generation_history if h['status'] in filter_status]
        
        if sort_order == 'Newest First':
            filtered_history.reverse()
        elif sort_order == 'Duration (Longest)':
            filtered_history.sort(key=lambda x: x.get('duration', 0), reverse=True)
        elif sort_order == 'Duration (Shortest)':
            filtered_history.sort(key=lambda x: x.get('duration', 999999))
        
        # Display history
        st.markdown("### 📋 History Entries")
        
        for i, entry in enumerate(filtered_history):
            with st.expander(f"{'✅' if entry['status'] == 'completed' else '❌'} {entry['url']} - {entry['timestamp'][:19]}"):
                col_h1, col_h2 = st.columns(2)
                
                with col_h1:
                    st.write(f"**Status:** {entry['status'].upper()}")
                    st.write(f"**URL:** {entry['url']}")
                    st.write(f"**Timestamp:** {entry['timestamp']}")
                
                with col_h2:
                    if 'duration' in entry:
                        st.write(f"**Duration:** {entry['duration']:.1f}s")
                    if 'output_path' in entry:
                        st.write(f"**Output:** `{entry['output_path']}`")
                    if 'error' in entry:
                        st.write(f"**Error:** {entry['error']}")
                
                # Action buttons for this entry
                if entry['status'] == 'completed' and 'output_path' in entry:
                    if os.path.exists(entry['output_path']):
                        if st.button(f"📄 View Docs", key=f"view_{i}"):
                            st.session_state.selected_repo = os.path.basename(os.path.dirname(entry['output_path']))
                            st.info("Switch to 'View Docs' tab to see the documentation")
    
    else:
        st.info("📭 No generation history yet")
        st.markdown("""
        History will appear here after you generate documentation.
        
        **Go to Generate Docs tab to get started!**
        """)

with tab4:
    st.header("Help & Documentation")
    
    # Quick start guide
    with st.expander("🚀 Quick Start Guide", expanded=True):
        st.markdown("""
        ### Getting Started with Codebase Genius
        
        **Step 1: Start the Jac Server**
```bash
        jac serve main.jac
```
        
        **Step 2: Launch Streamlit**
```bash
        streamlit run app.py
```
        
        **Step 3: Generate Documentation**
        1. Go to the **Generate Docs** tab
        2. Enter a GitHub repository URL
        3. Click the **Generate** button
        4. Wait for processing (1-5 minutes)
        5. View or download your documentation!
        
        **Step 4: View Results**
        - Switch to the **View Docs** tab
        - Select your repository
        - Read or download the generated documentation
        """)
    
    # Requirements
    with st.expander("📋 System Requirements"):
        st.markdown("""
        ### Software Requirements
        
        - **Python:** 3.9 or higher
        - **JacLang:** 0.7.0 or higher
        - **Git:** For cloning repositories
        - **API Key:** OpenAI or Google Gemini
        
        ### Supported Repositories
        
        - ✅ Public GitHub repositories
        - ✅ Python projects
        - ✅ Jac projects
        - ⚠️ Other languages (limited support)
        - ❌ Private repositories (requires authentication)
        
        ### Recommended Repository Size
        
        - **Small:** < 20 files (1-2 minutes)
        - **Medium:** 20-50 files (2-4 minutes)
        - **Large:** 50-100 files (4-8 minutes)
        - **Very Large:** > 100 files (may timeout)
        """)
    
    # Troubleshooting
    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        ### Common Issues and Solutions
        
        **❌ "Cannot connect to Jac server"**
        - Make sure the Jac server is running: `jac serve main.jac`
        - Check the server URL in the sidebar
        - Verify port 8000 is not blocked by firewall
        
        **❌ "API key not found"**
        - Create a `.env` file in your project root
        - Add your API key: `OPENAI_API_KEY=your-key-here`
        - Restart the Jac server
        
        **⏱️ "Request timeout"**
        - Try with a smaller repository
        - Increase timeout in Advanced Options
        - Check your internet connection
        
        **❌ "Failed to clone repository"**
        - Verify the URL is correct
        - Ensure the repository is public
        - Check your internet connection
        
        **📉 "Documentation quality is poor"**
        - Ensure the repository has a README
        - Verify Python/Jac files follow conventions
        - Try a well-documented repository first
        """)
    
    # Features
    with st.expander("✨ Features & Capabilities"):
        st.markdown("""
        ### What Codebase Genius Can Do
        
        **📊 Code Analysis**
        - Extract functions, classes, and methods
        - Identify code relationships
        - Calculate complexity metrics
        - Build dependency graphs
        
        **📝 Documentation Generation**
        - Professional markdown format
        - AI-powered overviews
        - Architecture diagrams (Mermaid)
        - API reference with examples
        - Installation instructions
        
        **🎨 Diagrams**
        - Class diagrams
        - Workflow diagrams
        - Relationship visualizations
        
        **🔍 Supported Languages**
        - Python (full support)
        - Jac (full support)
        - JavaScript (partial)
        - Java (partial)
        - Others (basic)
        """)
    
    # API Reference
    with st.expander("🔌 API Reference"):
        st.markdown("""
        ### Using the API Directly
        
        **Endpoint:** `POST /walker/DocumentRepository`
        
        **Request Body:**
```json
        {
            "github_url": "https://github.com/user/repo",
            "output_dir": "./outputs"
        }
```
        
        **Response:**
```json
        {
            "status": "completed",
            "repository": "repo-name",
            "output_path": "./outputs/repo-name/docs.md",
            "timestamp": "2024-01-01T12:00:00"
        }
```
        
        **Example using curl:**
```bash
        curl -X POST http://localhost:8000/walker/DocumentRepository \\
          -H "Content-Type: application/json" \\
          -d '{"github_url": "https://github.com/user/repo"}'
```
        
        **Example using Python:**
```python
        import requests
        
        response = requests.post(
            "http://localhost:8000/walker/DocumentRepository",
            json={"github_url": "https://github.com/user/repo"}
        )
        
        print(response.json())
```
        """)
    
    # Contact & Support
    with st.expander("📞 Support & Contact"):
        st.markdown("""
        ### Getting Help
        
        **Documentation:**
        - README.md - Full setup guide
        - QUICKSTART.md - Quick start guide
        - WALKTHROUGH.md - Implementation details
        
        **Resources:**
        - [Jac Documentation](https://www.jac-lang.org/)
        - [Python AST Module](https://docs.python.org/3/library/ast.html)
        - [Streamlit Docs](https://docs.streamlit.io/)
        
        **Tips for Best Results:**
        1. Start with small repositories
        2. Ensure repositories have README files
        3. Use well-structured Python/Jac code
        4. Check server logs for detailed errors
        5. Try example repositories first
        """)
    
    st.markdown("---")
    
    # Version info
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; color: #666;">
        <p><strong>Codebase Genius v1.0.0</strong></p>
        <p>Built with ❤️ using Jac, Python & AI</p>
        <p>© 2024 Codebase Genius Project</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem 0;">
    <p>🧠 <strong>Codebase Genius</strong> | Powered by Jac & AI | <a href="https://github.com/your-repo">GitHub</a></p>
</div>
""", unsafe_allow_html=True)