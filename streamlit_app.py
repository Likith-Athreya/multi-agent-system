import streamlit as st
import json
import tempfile
import os
from datetime import datetime
from pathlib import Path
import pandas as pd
from multiagent_system import MultiAgentSystem, ProcessingResult
import logging

# Configure page
st.set_page_config(
    page_title="Multi-Agent AI Document Processor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .agent-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        color: white;
        font-weight: bold;
        margin: 0.25rem;
        display: inline-block;
    }
    .json-agent { background-color: #ff7f0e; }
    .email-agent { background-color: #2ca02c; }
    .pdf-agent { background-color: #d62728; }
    .classifier { background-color: #9467bd; }
    
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
    .result-container {
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'processing_history' not in st.session_state:
    st.session_state.processing_history = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'system' not in st.session_state:
    st.session_state.system = None
if 'show_raw_data' not in st.session_state:
    st.session_state.show_raw_data = {}

def initialize_system(api_key):
    """Initialize the multi-agent system"""
    try:
        system = MultiAgentSystem(api_key)
        st.session_state.system = system
        return True, "System initialized successfully!"
    except Exception as e:
        return False, f"Failed to initialize system: {str(e)}"

def process_uploaded_file(uploaded_file, thread_id=None):
    """Process an uploaded file"""
    if not st.session_state.system:
        return None, "System not initialized. Please enter a valid API key."
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        # Process the file
        result = st.session_state.system.process_file(tmp_file_path, thread_id)
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        # Add to history
        st.session_state.processing_history.append({
            'timestamp': result.timestamp,
            'filename': uploaded_file.name,
            'result': result
        })
        
        return result, None
        
    except Exception as e:
        return None, f"Error processing file: {str(e)}"

def process_text_input(text_content, filename="text_input.txt", thread_id=None):
    """Process text input directly"""
    if not st.session_state.system:
        return None, "System not initialized. Please enter a valid API key."
    
    try:
        result = st.session_state.system.process_input(text_content, filename, thread_id)
        
        # Add to history
        st.session_state.processing_history.append({
            'timestamp': result.timestamp,
            'filename': filename,
            'result': result
        })
        
        return result, None
        
    except Exception as e:
        return None, f"Error processing text: {str(e)}"

def display_result(result: ProcessingResult, container_key=None):
    """Display processing result in a formatted way"""
    
    # Create unique key for this result
    if container_key is None:
        container_key = result.thread_id
    
    # Status indicator
    if result.success:
        st.success("✅ Processing Successful")
    else:
        st.error("❌ Processing Failed")
    
    # Basic information in a container
    with st.container():
        st.markdown('<div class="result-container">', unsafe_allow_html=True)
        
        # Agent and classification info
        col1, col2, col3 = st.columns(3)
        with col1:
            agent_class = result.agent_type.replace('_', '-')
            st.markdown(f'<span class="agent-badge {agent_class}">{result.agent_type.upper()}</span>', 
                       unsafe_allow_html=True)
        with col2:
            st.write(f"**Thread ID:** {result.thread_id}")
        with col3:
            st.write(f"**Timestamp:** {result.timestamp[:19]}")
        
        # Classification details
        st.subheader("📊 Classification")
        class_col1, class_col2, class_col3 = st.columns(3)
        with class_col1:
            st.metric("Format", result.classification.get('format', 'Unknown'))
        with class_col2:
            st.metric("Intent", result.classification.get('intent', 'Unknown'))
        with class_col3:
            st.metric("Confidence", result.classification.get('confidence', 'Unknown'))
        
        if result.success:
            # Display extracted data based on agent type
            st.subheader("📋 Extracted Data")
            
            if result.agent_type == "json_agent":
                display_json_result(result.data, container_key)
            elif result.agent_type == "email_agent":
                display_email_result(result.data, container_key)
            else:
                st.json(result.data)
        else:
            # Display errors
            st.subheader("❌ Errors")
            for error in result.errors or []:
                st.error(error)
        
        st.markdown('</div>', unsafe_allow_html=True)

def display_json_result(data, container_key):
    """Display JSON agent results"""
    extracted = data.get('extracted_data', {})
    anomalies = data.get('anomalies', [])
    
    # Extracted fields
    st.write("**Extracted Fields:**")
    if extracted:
        df = pd.DataFrame(list(extracted.items()), columns=['Field', 'Value'])
        st.dataframe(df, use_container_width=True)
    else:
        st.write("No fields extracted")
    
    # Schema compliance
    compliance = data.get('schema_compliance', False)
    if compliance:
        st.success("✅ Schema Compliant")
    else:
        st.warning("⚠️ Schema Issues Detected")
    
    # Anomalies
    if anomalies:
        st.write("**⚠️ Anomalies Detected:**")
        for anomaly in anomalies:
            st.warning(anomaly)
    
    # Toggle for raw data
    show_raw_key = f"show_raw_{container_key}_json"
    if show_raw_key not in st.session_state.show_raw_data:
        st.session_state.show_raw_data[show_raw_key] = False
    
    if st.button(f"{'Hide' if st.session_state.show_raw_data[show_raw_key] else 'Show'} Original Data", 
                 key=f"toggle_raw_{container_key}_json"):
        st.session_state.show_raw_data[show_raw_key] = not st.session_state.show_raw_data[show_raw_key]
    
    if st.session_state.show_raw_data[show_raw_key]:
        st.json(data.get('original_data', {}))

def display_email_result(data, container_key):
    """Display email agent results"""
    extracted = data.get('extracted_info', {})
    urgency = data.get('urgency_level', 'unknown')
    crm_data = data.get('crm_formatted', {})
    
    # Key information
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📧 Email Details:**")
        st.write(f"**Sender:** {extracted.get('sender', 'N/A')}")
        st.write(f"**Subject:** {extracted.get('subject', 'N/A')}")
        st.write(f"**Sentiment:** {extracted.get('sentiment', 'N/A')}")
        
        # Urgency with color coding
        urgency_colors = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        urgency_icon = urgency_colors.get(urgency, '⚪')
        st.write(f"**Urgency:** {urgency_icon} {urgency.upper()}")
    
    with col2:
        st.write("**🎯 CRM Data:**")
        st.write(f"**Status:** {crm_data.get('status', 'N/A')}")
        st.write(f"**Priority:** {crm_data.get('priority', 'N/A')}")
        st.write(f"**Category:** {crm_data.get('category', 'N/A')}")
        st.write(f"**Contact:** {crm_data.get('contact_name', 'N/A')}")
    
    # Key points
    key_points = extracted.get('key_points', [])
    if key_points:
        st.write("**🔑 Key Points:**")
        for i, point in enumerate(key_points, 1):
            # Truncate very long points
            display_point = point[:200] + "..." if len(point) > 200 else point
            st.write(f"{i}. {display_point}")
    
    # Action items
    actions = extracted.get('action_items', [])
    if actions:
        st.write("**✅ Action Items:**")
        for i, action in enumerate(actions, 1):
            st.write(f"{i}. {action}")
    
    # Toggle for email structure
    show_structure_key = f"show_structure_{container_key}_email"
    if show_structure_key not in st.session_state.show_raw_data:
        st.session_state.show_raw_data[show_structure_key] = False
    
    if st.button(f"{'Hide' if st.session_state.show_raw_data[show_structure_key] else 'Show'} Email Structure", 
                 key=f"toggle_structure_{container_key}_email"):
        st.session_state.show_raw_data[show_structure_key] = not st.session_state.show_raw_data[show_structure_key]
    
    if st.session_state.show_raw_data[show_structure_key]:
        st.json(data.get('email_structure', {}))

def main():
    """Main Streamlit app"""
    
    # Header
    st.markdown('<h1 class="main-header">🤖 Multi-Agent AI Document Processor</h1>', 
                unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "OpenRouter API Key",
            type="password",
            value=st.session_state.api_key,
            help="Enter your OpenRouter API key to initialize the system"
        )
        
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
            if api_key:
                success, message = initialize_system(api_key)
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        # System status
        st.subheader("🔧 System Status")
        if st.session_state.system:
            st.success("✅ System Ready")
        else:
            st.error("❌ System Not Initialized")
        
        # Processing statistics
        if st.session_state.processing_history:
            st.subheader("📊 Statistics")
            total_processed = len(st.session_state.processing_history)
            successful = len([h for h in st.session_state.processing_history 
                            if h['result'].success])
            st.metric("Total Processed", total_processed)
            st.metric("Success Rate", f"{(successful/total_processed)*100:.1f}%")
        
        # Clear history button
        if st.button("🗑️ Clear History"):
            st.session_state.processing_history = []
            st.session_state.show_raw_data = {}
            st.success("History cleared!")
    
    # Main interface tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📄 File Upload", "✏️ Text Input", "📊 Results", "📈 History"])
    
    with tab1:
        st.header("📄 File Upload Processing")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose files to process",
            accept_multiple_files=True,
            type=['json', 'txt', 'pdf', 'eml'],
            help="Supported formats: JSON, TXT, PDF, EML"
        )
        
        # Thread ID input
        thread_id = st.text_input(
            "Thread ID (optional)",
            placeholder="Leave blank for auto-generation",
            help="Specify a thread ID to group related documents"
        )
        
        # Process files
        if uploaded_files and st.button("🚀 Process Files", type="primary"):
            if not st.session_state.system:
                st.error("Please enter a valid API key first!")
            else:
                progress_bar = st.progress(0)
                
                for i, uploaded_file in enumerate(uploaded_files):
                    st.write(f"Processing: **{uploaded_file.name}**")
                    
                    # Generate thread ID if not provided
                    current_thread_id = thread_id if thread_id else f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"
                    
                    result, error = process_uploaded_file(uploaded_file, current_thread_id)
                    
                    if result:
                        st.success(f"✅ Processed {uploaded_file.name}")
                        # Create a container for each result
                        with st.container():
                            display_result(result, f"file_{i}")
                    else:
                        st.error(f"Error processing {uploaded_file.name}: {error}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                st.success(f"✅ Completed processing {len(uploaded_files)} file(s)")
    
    with tab2:
        st.header("✏️ Direct Text Input")
        
        # Text input methods
        input_method = st.radio(
            "Input Method",
            ["Text Area", "JSON Editor"],
            horizontal=True
        )
        
        if input_method == "Text Area":
            text_content = st.text_area(
                "Enter text content",
                height=300,
                placeholder="Paste email content, document text, or any other text to process..."
            )
            filename = st.text_input("Filename (optional)", value="text_input.txt")
        else:
            st.write("**JSON Editor:**")
            default_json = {
                "document_type": "example",
                "content": "Your JSON content here"
            }
            text_content = st.text_area(
                "Enter JSON content",
                value=json.dumps(default_json, indent=2),
                height=300
            )
            filename = st.text_input("Filename (optional)", value="json_input.json")
        
        # Thread ID
        thread_id_text = st.text_input(
            "Thread ID (optional)",
            placeholder="Leave blank for auto-generation",
            key="text_thread_id"
        )
        
        # Process text
        if st.button("🚀 Process Text", type="primary"):
            if not text_content.strip():
                st.error("Please enter some content to process!")
            elif not st.session_state.system:
                st.error("Please enter a valid API key first!")
            else:
                current_thread_id = thread_id_text if thread_id_text else f"text_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                with st.spinner("Processing..."):
                    result, error = process_text_input(text_content, filename, current_thread_id)
                
                if result:
                    st.success("✅ Processing completed!")
                    display_result(result, "text_input")
                else:
                    st.error(f"Processing failed: {error}")
    
    with tab3:
        st.header("📊 Latest Results")
        
        if st.session_state.processing_history:
            # Show latest result
            latest = st.session_state.processing_history[-1]
            st.subheader(f"📄 Latest: {latest['filename']}")
            display_result(latest['result'], "latest")
            
            # Quick stats
            st.subheader("📈 Quick Stats")
            col1, col2, col3, col4 = st.columns(4)
            
            agent_counts = {}
            intent_counts = {}
            for entry in st.session_state.processing_history:
                agent = entry['result'].agent_type
                intent = entry['result'].classification.get('intent', 'Unknown')
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            with col1:
                st.metric("Total Files", len(st.session_state.processing_history))
            with col2:
                successful = len([h for h in st.session_state.processing_history if h['result'].success])
                st.metric("Successful", successful)
            with col3:
                most_common_agent = max(agent_counts, key=agent_counts.get) if agent_counts else "None"
                st.metric("Top Agent", most_common_agent)
            with col4:
                most_common_intent = max(intent_counts, key=intent_counts.get) if intent_counts else "None"
                st.metric("Top Intent", most_common_intent)
        else:
            st.info("No processing results yet. Upload files or enter text to get started!")
    
    with tab4:
        st.header("📈 Processing History")
        
        if st.session_state.processing_history:
            # Filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                agent_filter = st.selectbox(
                    "Filter by Agent",
                    ["All"] + list(set(h['result'].agent_type for h in st.session_state.processing_history))
                )
            
            with col2:
                status_filter = st.selectbox(
                    "Filter by Status",
                    ["All", "Success", "Failed"]
                )
            
            with col3:
                limit = st.number_input("Show last N results", min_value=5, max_value=100, value=20)
            
            # Apply filters
            filtered_history = st.session_state.processing_history[-limit:]
            
            if agent_filter != "All":
                filtered_history = [h for h in filtered_history if h['result'].agent_type == agent_filter]
            
            if status_filter != "All":
                success_filter = status_filter == "Success"
                filtered_history = [h for h in filtered_history if h['result'].success == success_filter]
            
            # Display history table
            if filtered_history:
                history_data = []
                for entry in reversed(filtered_history):  # Most recent first
                    result = entry['result']
                    history_data.append({
                        'Timestamp': result.timestamp[:19],
                        'Filename': entry['filename'],
                        'Agent': result.agent_type,
                        'Format': result.classification.get('format', 'Unknown'),
                        'Intent': result.classification.get('intent', 'Unknown'),
                        'Status': '✅ Success' if result.success else '❌ Failed',
                        'Thread ID': result.thread_id
                    })
                
                df = pd.DataFrame(history_data)
                st.dataframe(df, use_container_width=True)
                
                # Detailed view selector
                st.subheader("📋 Detailed View")
                if len(filtered_history) > 0:
                    selected_index = st.selectbox(
                        "Select entry to view details",
                        range(len(filtered_history)),
                        format_func=lambda x: f"{filtered_history[-(x+1)]['filename']} - {filtered_history[-(x+1)]['result'].timestamp[:19]}"
                    )
                    
                    selected_entry = filtered_history[-(selected_index+1)]
                    st.write(f"**File:** {selected_entry['filename']}")
                    display_result(selected_entry['result'], f"history_{selected_index}")
            else:
                st.info("No results match the selected filters.")
        else:
            st.info("No processing history available yet.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "Multi-Agent AI Document Processor | Built with Streamlit"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()