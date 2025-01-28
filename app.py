import streamlit as st
import requests
from streamlit_option_menu import option_menu
import time
import json
import base64
import tempfile
import os

# Initialize session state
if 'token' not in st.session_state:
    st.session_state['token'] = None

def login():
    st.markdown("""
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
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username = st.text_input("📧 Email or Username", key='login_username', 
                                 placeholder="Enter your email or username")
        password = st.text_input("🔒 Password", type="password", key='login_password', 
                                 placeholder="Enter your password")

        remember = st.checkbox("Remember me", value=True)

        if st.button("Sign In"):
            if username and password:
                with st.spinner("Authenticating..."):
                    data = {'username': username, 'password': password}
                    response = requests.post('https://dev.razonica.in/login', json=data)
                    if response.status_code == 200:
                        st.success("Login successful! Redirecting...")
                        st.session_state['token'] = response.json()['token']
                        st.session_state['messages'] = []
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")
            else:
                st.warning("Please enter both username and password")

def signup():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username = st.text_input("📧 Email or Username", key='signup_username', 
                                 placeholder="Enter your email or username")
        password = st.text_input("🔒 Password", type="password", key='signup_password', 
                                 placeholder="Choose a strong password")
        confirm_password = st.text_input("🔒 Confirm Password", type="password", 
                                         key='confirm_password', 
                                         placeholder="Confirm your password")

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
                    response = requests.post('https://dev.razonica.in/register', json=data)
                    if response.status_code == 201:
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error(response.json().get('message', 'Registration failed'))
            else:
                st.warning("Please fill in all fields")

def logout():
    st.session_state['token'] = None
    st.session_state['messages'] = []
    st.success("Logged out")
    st.rerun()

def display_files():
    st.subheader("Uploaded Files")
    headers = {'Authorization': 'Bearer ' + st.session_state['token']}
    response = requests.get('https://dev.razonica.in/list_uploaded_files', headers=headers)
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
    response = requests.get('https://dev.razonica.in/list_uploaded_files', headers=headers)
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
                    headers = {
                        'Authorization': 'Bearer ' + st.session_state['token'],
                        'Content-Type': 'application/json'
                    }
                    delete_response = requests.post('https://dev.razonica.in/delete_upload', headers=headers, json=data)
                    if delete_response.status_code == 200:
                        st.success(f"Deleted {filename}")
                        st.rerun()
                    else:
                        try:
                            error_message = delete_response.json().get('message', 'Unknown error')
                        except:
                            error_message = delete_response.text or 'Unknown error'
                        st.error(f"Failed to delete {filename}: {error_message}")
        else:
            st.write("No files uploaded yet.")
    else:
        st.error("Failed to fetch files.")

def main():
    st.set_page_config(layout="wide")

    if st.session_state['token']:
        # Header with logout
        header_cols = st.columns([8, 1])
        with header_cols[0]:
            st.title("DataDash - AI Powered Business Insights")
        with header_cols[1]:
            st.write("")
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
                token = st.session_state['token']
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
                    <form action="https://dev.razonica.in/upload" class="dropzone" id="fileDropzone">
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
                                        fetch('https://dev.razonica.in/delete', {{
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
            if 'messages' not in st.session_state:
                st.session_state['messages'] = []
            if 'graph_mode' not in st.session_state:
                st.session_state['graph_mode'] = False
            if 'web_mode' not in st.session_state:
                st.session_state['web_mode'] = False

            chat_container = st.container()

            # Fetch user files
            headers = {'Authorization': 'Bearer ' + st.session_state['token']}
            response = requests.get('https://dev.razonica.in/get_user_files', headers=headers)
            if response.status_code == 200:
                files_data = response.json().get('files', [])
                options = st.multiselect("Select files to query", files_data, [])
            else:
                st.error("Failed to fetch user files.")
                options = []

            col_cb1, col_cb2 = st.columns(2)
            with col_cb1:
                graph_mode = st.checkbox("Generate Graphs with answers?", value=False)
            with col_cb2:
                web_mode = st.checkbox("Web Cross-Check?", value=False)

            st.session_state['graph_mode'] = graph_mode
            st.session_state['web_mode'] = web_mode

            col1, col2 = st.columns([6, 1])
            with col1:
                prompt = st.chat_input("Type your message here...")
            with col2:
                if st.button("Clear Chat"):
                    st.session_state['messages'] = []
                    st.rerun()

            # Display chat so far
            with chat_container:
                for message in st.session_state['messages']:
                    if message["role"] == "assistant":
                        with st.chat_message("assistant"):
                            st.markdown(message["content"], unsafe_allow_html=True)
                            # DECODE any base64 image
                            if "image" in message and message["image"]:
                                try:
                                    decoded_image = base64.b64decode(message["image"])
                                    st.image(decoded_image, caption="Generated Chart")
                                except Exception as e:
                                    st.warning(f"Could not decode chart image: {e}")

                            # Show web agent output if present
                            if "web_agent" in message and message["web_agent"]:
                                st.markdown(
                                    f"**WebAgent Output:**\n\n{message['web_agent']}",
                                    unsafe_allow_html=True
                                )
                            
                            if "web_agent_citations" in message and message["web_agent_citations"]:
                                top_5_cits = message["web_agent_citations"][:5]
                                st.markdown("**Top 5 Citations:**")
                                for i, cit in enumerate(top_5_cits, start=1):
                                    st.markdown(f"{i}. {cit}")
                    else:
                        with st.chat_message("user"):
                            st.write(message["content"])

            if prompt:
                # show user message
                with st.chat_message("user"):
                    st.write(prompt)
                st.session_state['messages'].append({"role": "user", "content": prompt})

                # Call AiCore
                with st.spinner("Thinking..."):
                    payload = {
                        "query": prompt,
                        "files": options,
                        "history": st.session_state['messages'],
                        "graph_mode": st.session_state['graph_mode'],
                        "web_mode": st.session_state['web_mode']
                    }
                    try:
                        run_response = requests.post(
                            'https://dev.razonica.in/run_aicore',
                            headers={'Authorization': 'Bearer ' + st.session_state['token']},
                            json=payload,
                            timeout=180
                        )
                        if run_response.status_code == 200:
                            resp_json = run_response.json()
                            final_answer = resp_json.get('answer', '')
                            image_b64 = resp_json.get('image', None)
                            web_data = resp_json.get('web_agent', None)

                            assistant_msg = {
                                "role": "assistant",
                                "content": final_answer
                            }
                            if image_b64:
                                assistant_msg["image"] = image_b64
                            if web_data and isinstance(web_data, dict):
                                assistant_msg["web_agent"] = web_data.get("openai_analysis", "")
                                assistant_msg["web_agent_citations"] = web_data.get("perplexity_citations", [])

                            st.session_state['messages'].append(assistant_msg)

                            # Display the assistant's response
                            with st.chat_message("assistant"):
                                st.markdown(final_answer, unsafe_allow_html=True)
                                # If there's a base64 image, decode + display
                                if image_b64:
                                    try:
                                        decoded_image = base64.b64decode(image_b64)
                                        st.image(decoded_image, caption="Generated Chart")
                                    except Exception as e:
                                        st.warning(f"Could not decode chart image: {e}")

                                if web_data and isinstance(web_data, dict):
                                    st.markdown(
                                        f"**WebAgent Output:**\n\n{web_data.get('openai_analysis', '')}",
                                        unsafe_allow_html=True
                                    )
                                    citations = web_data.get("perplexity_citations", [])
                                    if citations:
                                        st.markdown("**Top 5 Citations:**")
                                        top_5_cits = citations[:5]
                                        for i, cit in enumerate(top_5_cits, start=1):
                                            st.markdown(f"{i}. {cit}")
                        else:
                            st.error(f"Error: Server returned status code {run_response.status_code}")

                    except requests.Timeout:
                        st.error("Error: Request timed out.")
                    except requests.RequestException as e:
                        st.error(f"Error: Connection failed - {str(e)}")

            # Auto scroll
            st.markdown(
                """
                <script>
                    var scrollingElement = (document.scrollingElement || document.body);
                    scrollingElement.scrollTop = scrollingElement.scrollHeight;
                </script>
                """,
                unsafe_allow_html=True
            )
    else:
        st.title("DataDash - AI Powered Business Insights")
        st.write("Please login or sign up.")

        st.markdown("""
            <style>
            .stTabs [data-baseweb="tab-list"] {
                gap: 24px;
                background-color: transparent;
            }
            .stTabs [data-baseweb="tab"] {
                height: 50px;
                padding: 10px 24px;
                background-color: transparent;
                border-radius: 4px;
                font-weight: 600;
                color: #808495;
            }
            .stTabs [aria-selected="true"] {
                background-color: #262730 !important;
                color: white !important;
            }
            </style>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        with tab1:
            login()
        with tab2:
            signup()

if __name__ == '__main__':
    main()
