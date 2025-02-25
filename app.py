import streamlit as st
import requests
import json
import base64
import os
import time
import matplotlib.pyplot as plt
import random
from streamlit_option_menu import option_menu

# ---------------------------
# Configuration
# ---------------------------
API_BASE = "https://dev.razonica.in"

# ---------------------------
# Session State Initialization
# ---------------------------
if "token" not in st.session_state:
    st.session_state["token"] = None
if "conversations" not in st.session_state:
    # Each item: {"user_message": str, "agent_replies": [{"agent": "AiCore"/"WebAgent"/"GraphAgent", "content": str, "type": "text"/"graph"}]}
    st.session_state["conversations"] = []
if "rendered_count" not in st.session_state:
    st.session_state["rendered_count"] = 0

# For demonstration (Graph placeholders), storing random data
if "demo_graph_data" not in st.session_state:
    st.session_state["demo_graph_data"] = [random.randint(1, 10) for _ in range(4)]
if "generated_graph_code" not in st.session_state:
    st.session_state["generated_graph_code"] = ""

# ---------------------------
# Utility to animate text
# ---------------------------
def animate_text(full_text, placeholder):
    """Gradually renders text character by character."""
    typed_text = ""
    for ch in full_text:
        typed_text += ch
        placeholder.markdown(typed_text)

# ---------------------------
# Helper functions for login, signup, logout
# ---------------------------
def login():
    st.markdown(
        """
        <style>
        .stTextInput > div > div > input {
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 12px 16px;
            border-radius: 8px;
            color: inherit;
            font-size: 16px;
            transition: all 0.3s ease;
            width: 100%;
        }
        .stTextInput > div > div > input:focus {
            border-color: #1a73e8;
            box-shadow: 0 0 0 2px rgba(26,115,232,0.2);
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("📧 Email or Username", key='login_username', placeholder="Enter your email or username")
        password = st.text_input("🔒 Password", type="password", key='login_password', placeholder="Enter your password")
        remember = st.checkbox("Remember me", value=True)
        if st.button("Sign In"):
            if username and password:
                with st.spinner("Authenticating..."):
                    data = {'username': username, 'password': password}
                    resp = requests.post(f"{API_BASE}/login", json=data)
                    if resp.status_code == 200:
                        st.success("Login successful! Redirecting...")
                        st.session_state['token'] = resp.json()['token']
                        st.session_state["conversations"] = []
                        st.session_state["rendered_count"] = 0
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")
            else:
                st.warning("Please enter both username and password")

def signup():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("📧 Email or Username", key='signup_username', placeholder="Enter your email or username")
        password = st.text_input("🔒 Password", type="password", key='signup_password', placeholder="Choose a strong password")
        confirm_password = st.text_input("🔒 Confirm Password", type="password", key='confirm_password', placeholder="Confirm your password")
        terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
        if st.button("Create Account"):
            if username and password and confirm_password:
                if password != confirm_password:
                    st.error("Passwords don't match!")
                    return
                if not terms:
                    st.error("Please accept the Terms of Service")
                    return
                with st.spinner("Creating your account..."):
                    data = {'username': username, 'password': password}
                    resp = requests.post(f"{API_BASE}/register", json=data)
                    if resp.status_code == 201:
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error(resp.json().get('message', 'Registration failed'))
            else:
                st.warning("Please fill in all fields")

def logout():
    st.session_state['token'] = None
    st.session_state["conversations"] = []
    st.session_state["rendered_count"] = 0
    st.success("Logged out")
    st.rerun()

# ---------------------------
# Display File Management
# ---------------------------
def display_files():
    st.subheader("Uploaded Files")
    headers = {'Authorization': 'Bearer ' + st.session_state['token']}
    response = requests.get(f"{API_BASE}/list_uploaded_files", headers=headers)
    if response.status_code == 200:
        files_data = response.json().get('files', [])
        if st.button("Refresh", key="refresh_files"):
            st.rerun()
        if files_data:
            unique_files = {}
            for file_info in files_data:
                filename = file_info['filename']
                if filename not in unique_files:
                    unique_files[filename] = file_info
            for filename, file_info in unique_files.items():
                status = file_info['status']
                col1, col2 = st.columns([6, 2])
                col1.write(filename)
                if status == 'completed':
                    col2.write("✅ Completed")
                elif status == 'processing':
                    col2.write("⏳ Processing")
                elif status == 'failed':
                    col2.write("❌ Failed")
                else:
                    col2.write("🕒 Pending")
        else:
            st.write("No files uploaded yet.")
    else:
        st.error("Failed to fetch files.")

def display_status():
    st.subheader("Status of Uploaded Files")
    headers = {'Authorization': 'Bearer ' + st.session_state['token']}
    response = requests.get(f"{API_BASE}/list_uploaded_files", headers=headers)
    if response.status_code == 200:
        files_data = response.json().get('files', [])
        if st.button("Refresh", key="refresh_status"):
            st.rerun()
        if files_data:
            for file_info in files_data:
                upload_id = file_info['id']
                filename = file_info['filename']
                status = file_info['status']
                col1, col2, col3 = st.columns([6, 2, 2])
                col1.write(filename)
                col2.write(status)
                if col3.button("Delete", key=f"delete_{upload_id}"):
                    data = {'upload_id': upload_id}
                    headers2 = {
                        'Authorization': 'Bearer ' + st.session_state['token'],
                        'Content-Type': 'application/json'
                    }
                    delete_response = requests.post(f"{API_BASE}/delete_upload", headers=headers2, json=data)
                    if delete_response.status_code == 200:
                        st.success(f"Deleted {filename}")
                        st.rerun()
                    else:
                        try:
                            error_message = delete_response.json().get('message', 'Unknown error')
                        except Exception:
                            error_message = delete_response.text or 'Unknown error'
                        st.error(f"Failed to delete {filename}: {error_message}")
        else:
            st.write("No files uploaded yet.")
    else:
        st.error("Failed to fetch files.")

# ---------------------------
# Render Chat (with partial typing & graphs)
# ---------------------------
def render_chat():
    """
    Renders all conversation turns with st.chat_message,
    ensuring old turns also display graphs in expanders,
    and that new turns show the code as well.
    """
    for i, convo in enumerate(st.session_state["conversations"]):
        is_new_turn = (i >= st.session_state["rendered_count"])

        # (A) User message
        with st.chat_message("user"):
            if is_new_turn:
                ph = st.empty()
                animate_text(convo["user_message"], ph)
            else:
                st.write(convo["user_message"])

        # (B) Agent replies
        for reply in convo["agent_replies"]:
            agent_name = reply.get("agent", "Agent")
            content = reply.get("content", "")
            msg_type = reply.get("type", "text")

            with st.chat_message("assistant"):
                if not is_new_turn:
                    # OLD turn (already rendered before)
                    if msg_type == "text":
                        st.markdown(f"**{agent_name}:** {content}")
                    elif msg_type == "graph":
                        st.markdown(f"**{agent_name}** generated a graph previously:")
                        if content.strip() == "":
                            st.write("Graph not generated.")
                        else:
                            # [MODIFIED] - Execute the old graph code in an expander
                            with st.expander("View Previous Graph"):
                                try:
                                    exec(content, globals())
                                except Exception as e:
                                    st.write(f"Error executing previous graph code: {e}")
                    st.markdown("---")
                else:
                    # NEW turn
                    if msg_type == "text":
                        ph = st.empty()
                        with st.spinner(f"{agent_name} is typing..."):
                            time.sleep(1)
                        animate_text(f"**{agent_name}:** {content}", ph)

                    elif msg_type == "graph":
                        ph = st.empty()
                        with st.spinner(f"{agent_name} is generating a graph..."):
                            time.sleep(2)
                        if content.strip() == "":
                            animate_text(f"**{agent_name}**: Graph not generated.", ph)
                        else:
                            # [MODIFIED] - Execute the new graph code
                            animate_text(f"**{agent_name}** generated a graph:", ph)
                            with st.expander("View Graph"):
                                try:
                                    exec(content, globals())
                                except Exception as e:
                                    st.write(f"Error executing graph code: {e}")
                    st.markdown("---")

    st.session_state["rendered_count"] = len(st.session_state["conversations"])

# ---------------------------
# Main Streamlit App
# ---------------------------
def main():
    st.set_page_config(layout="wide")
    
    if st.session_state["token"]:
        # Authenticated
        header_cols = st.columns([8, 1])
        with header_cols[0]:
            st.title("DataDash - AI Powered Business Insights")
        with header_cols[1]:
            if st.button("Logout"):
                logout()
        
        with st.sidebar:
            page = option_menu(
                "Menu Options", 
                ["Home", "Data Insights"],  
                icons=['house', 'file-text'], 
                menu_icon="list",
                styles={
                    "container": {"padding": "0!important", "background-color": "transparent"},
                    "icon": {"color": "#ffffff", "font-size": "20px"},
                    "nav-link": {
                        "font-size": "16px", 
                        "text-align": "left", 
                        "margin": "2px", 
                        "--hover-color": "#ff2b2b",
                        "color": "white"
                    },
                    "nav-link-selected": {"background-color": "#ff2b2b"},
                }
            )
        
        if page == "Home":
            tab1, tab2, tab3 = st.tabs(["Upload", "Uploaded", "Status"])

            with tab1:
                # Dropzone for uploading
                token = st.session_state["token"]
                dropzone_html = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <style>
                        :root {{
                            --primary-color: #BB86FC;
                            --background-color: #F0F2F6;
                            --text-color: #333333;
                            --font: "Source Sans Pro", sans-serif;
                        }}
                        .dropzone {{
                            border: 2px dashed var(--primary-color);
                            border-radius: 5px;
                            background: var(--background-color);
                            padding: 20px;
                            width: 100%;
                            color: var(--text-color);
                            font-family: var(--font);
                            max-height: 500px;
                            overflow-y: auto;
                        }}
                        .dropzone .dz-message {{
                            font-size: 1.2em;
                            color: var(--text-color);
                        }}
                        .dz-preview {{
                            position: relative;
                            background: var(--background-color);
                            border: 1px solid var(--primary-color);
                            border-radius: 5px;
                            padding: 10px;
                            margin-top: 10px;
                        }}
                        .delete-icon {{
                            position: absolute;
                            top: -10px;
                            right: -10px;
                            width: 24px;
                            height: 24px;
                            cursor: pointer;
                            z-index: 1000;
                            transition: transform 0.2s;
                        }}
                        .delete-icon:hover {{
                            transform: scale(1.1);
                        }}
                        ::-webkit-scrollbar {{
                            width: 8px;
                        }}
                        ::-webkit-scrollbar-track {{
                            background: var(--background-color);
                        }}
                        ::-webkit-scrollbar-thumb {{
                            background-color: var(--primary-color);
                            border-radius: 4px;
                        }}
                    </style>
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/dropzone/5.9.3/dropzone.min.css">
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/dropzone/5.9.3/dropzone.min.js"></script>
                </head>
                <body>
                    <form action="{API_BASE}/upload" class="dropzone" id="fileDropzone">
                        <div class="dz-message">
                            Drag and drop files here or click to upload.
                        </div>
                    </form>
                    <script>
                        const jwtToken = "{token}";
                        Dropzone.options.fileDropzone = {{
                            paramName: "file",
                            maxFilesize: 1024,
                            uploadMultiple: false,
                            parallelUploads: 2,
                            timeout: 300000,
                            clickable: true,
                            autoProcessQueue: true,
                            init: function() {{
                                this.on("sending", function(file, xhr, formData) {{
                                    xhr.setRequestHeader("Authorization", "Bearer " + jwtToken);
                                }});
                                this.on("addedfile", function(file) {{
                                    let deleteIcon = document.createElement("img");
                                    deleteIcon.src = "https://cdn2.iconfinder.com/data/icons/user-interface-presicon-line/64/cross-512.png";
                                    deleteIcon.className = "delete-icon";
                                    file.previewElement.appendChild(deleteIcon);
                                    deleteIcon.addEventListener("click", function(e) {{
                                        e.preventDefault();
                                        e.stopPropagation();
                                        this.removeFile(file);
                                        fetch('{API_BASE}/delete', {{
                                            method: 'POST',
                                            headers: {{
                                                'Content-Type': 'application/json',
                                                'Authorization': 'Bearer ' + jwtToken
                                            }},
                                            body: JSON.stringify({{ filename: file.name }})
                                        }})
                                        .then(response => {{
                                            if (response.ok) {{
                                                return response.json();
                                            }} else {{
                                                throw new Error('Failed to delete file');
                                            }}
                                        }})
                                        .then(data => {{
                                            if (data.success) {{
                                                console.log('File deleted successfully');
                                            }} else {{
                                                console.error('Error deleting file:', data.message || 'Unknown error');
                                            }}
                                        }})
                                        .catch(error => {{
                                            console.error('Error:', error);
                                        }});
                                    }}.bind(this));
                                }});
                            }}
                        }};
                    </script>
                </body>
                </html>
                """
                st.components.v1.html(dropzone_html, height=600)

            with tab2:
                display_files()

            with tab3:
                display_status()

        elif page == "Data Insights":
            # --------------------------
            # Chat interface with partial typing
            # --------------------------
            headers_req = {'Authorization': f"Bearer {st.session_state['token']}"}
            # Fetch user files for selection
            file_resp = requests.get(f"{API_BASE}/get_user_files", headers=headers_req)
            if file_resp.status_code == 200:
                all_files_data = file_resp.json().get('files', [])
                selected_files = st.multiselect("Select files to query", all_files_data, [])
            else:
                st.error("Failed to fetch user files.")
                selected_files = []

            col_cb1, col_cb2 = st.columns(2)
            with col_cb1:
                graph_mode = st.checkbox("Generate Graph with answer?", value=False)
            with col_cb2:
                web_mode = st.checkbox("Web Cross-Check?", value=False)

            # Render existing conversation
            chat_container = st.container()
            with chat_container:
                render_chat()

            # Input form for user message
            with st.form("chat_input_form", clear_on_submit=True):
                user_input = st.text_input("Enter your message:")
                submitted = st.form_submit_button("Send")

                if submitted and user_input:
                    # (1) Append new user turn
                    new_turn = {
                        "user_message": user_input,
                        "agent_replies": []
                    }
                    st.session_state["conversations"].append(new_turn)

                    # (2) AiCore request
                    ai_payload = {
                        "query": user_input,
                        "files": selected_files,
                        "history": st.session_state["conversations"]
                    }
                    try:
                        with st.spinner("ExcelAgent and TextAgent are working..."):
                            r = requests.post(
                                f"{API_BASE}/run_aicore",
                                headers=headers_req,
                                json=ai_payload,
                                timeout=180
                            )
                        if r.status_code == 200:
                            aicore_result = r.json()  # e.g. {"ExcelAgent": "...", "TextAgent": "..."}

                            excel_text = aicore_result.get("ExcelAgent", "")
                            text_text = aicore_result.get("TextAgent", "")

                            # If excel text is non-empty
                            if excel_text.strip():
                                st.session_state["conversations"][-1]["agent_replies"].append(
                                    {"agent": "ExcelAgent", "content": excel_text, "type": "text"}
                                )
                            # If text agent has content
                            if text_text.strip():
                                st.session_state["conversations"][-1]["agent_replies"].append(
                                    {"agent": "TextAgent", "content": text_text, "type": "text"}
                                )
                        else:
                            st.session_state["conversations"][-1]["agent_replies"].append(
                                {"agent": "AiCore", "content": "[AiCore] Error from backend.", "type": "text"}
                            )
                    except Exception as exc:
                        st.session_state["conversations"][-1]["agent_replies"].append(
                            {"agent": "AiCore", "content": f"[AiCore] Exception: {exc}", "type": "text"}
                        )

                    # (3) Optionally call WebAgent
                    if web_mode:
                        try:
                            with st.spinner("WebAgent is working..."):
                                w_payload = {
                                    "query": user_input,
                                    "excel_result": aicore_result.get("ExcelAgent", "") if 'aicore_result' in locals() else "",
                                    "history": st.session_state["conversations"]
                                }
                                wresp = requests.post(
                                    f"{API_BASE}/run_web_agent",
                                    headers=headers_req,
                                    json=w_payload,
                                    timeout=180
                                )
                            if wresp.status_code == 200:
                                web_data = wresp.json()  # {"agent":"WebAgent","result":{...}}
                                if "result" in web_data:
                                    web_analysis = web_data["result"].get("openai_analysis", "")
                                    st.session_state["conversations"][-1]["agent_replies"].append(
                                        {"agent": "WebAgent", "content": web_analysis, "type": "text"}
                                    )
                            else:
                                st.session_state["conversations"][-1]["agent_replies"].append(
                                    {"agent": "WebAgent", "content": "[WebAgent] Error from backend.", "type": "text"}
                                )
                        except Exception as exc:
                            st.session_state["conversations"][-1]["agent_replies"].append(
                                {"agent": "WebAgent", "content": f"[WebAgent] Exception: {exc}", "type": "text"}
                            )

                    # (4) Optionally call GraphAgent
                    if graph_mode:
                        graph_payload = {
                            "query": user_input,
                            "excel_result": aicore_result.get("ExcelAgent", "") if 'aicore_result' in locals() else ""
                        }
                        try:
                            with st.spinner("GraphAgent is working..."):
                                gresp = requests.post(
                                    f"{API_BASE}/generate_streamlit_graph",
                                    headers=headers_req,
                                    json=graph_payload,
                                    timeout=180
                                )
                            if gresp.status_code == 200:
                                graph_code = gresp.json().get("code", "")
                                # [MODIFIED] Save the actual code in the conversation turn, so old & new can display
                                st.session_state["generated_graph_code"] = graph_code
                                st.session_state["conversations"][-1]["agent_replies"].append(
                                    {"agent": "GraphAgent", "content": graph_code, "type": "graph"}  # [MODIFIED]
                                )
                            else:
                                st.session_state["conversations"][-1]["agent_replies"].append(
                                    {"agent": "GraphAgent", "content": "[GraphAgent] Could not generate chart code.", "type": "text"}
                                )
                        except Exception as exc:
                            st.session_state["conversations"][-1]["agent_replies"].append(
                                {"agent": "GraphAgent", "content": f"[GraphAgent] Exception: {exc}", "type": "text"}
                            )

                    # Rerun so the partial-typing animation is triggered for the new turn
                    st.rerun()

            if st.button("Clear Chat"):
                st.session_state["conversations"] = []
                st.session_state["rendered_count"] = 0
                st.rerun()

        else:
            # Not authenticated: show Login / Sign Up
            st.title("DataDash - AI Powered Business Insights")
            st.write("Please login or sign up.")
            tab1, tab2 = st.tabs(["Login", "Sign Up"])
            with tab1:
                login()
            with tab2:
                signup()


# Entry point
if __name__ == '__main__':
    main()
