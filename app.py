# streamlit_app.py
import streamlit as st
import requests
from streamlit_option_menu import option_menu
import time
import requests
import json

# Streamlit app configuration
st.set_page_config(layout="wide")

# Initialize session state
if 'token' not in st.session_state:
    st.session_state['token'] = None

def login():
    st.markdown("""
        <style>
        /* Input field styling */
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

    # st.title("Welcome Back")
    # st.markdown("Sign in to continue to DataDash")
    
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
                    response = requests.post('https://1d1d-116-73-245-216.ngrok-free.app/login', json=data)
                    if response.status_code == 200:
                        st.success("Login successful! Redirecting...")
                        st.session_state['token'] = response.json()['token']
                        st.session_state['messages'] = []  # Add this line
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")
            else:
                st.warning("Please enter both username and password")

def signup():
    # st.title("Create Your Account")
    # st.markdown("Join DataDash and unlock powerful insights")
    
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
                    response = requests.post('https://1d1d-116-73-245-216.ngrok-free.app/register', json=data)
                    if response.status_code == 201:
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error(response.json().get('message', 'Registration failed'))
            else:
                st.warning("Please fill in all fields")

def logout():
    st.session_state['token'] = None
    st.session_state['messages'] = []  # Add this line
    st.success("Logged out")
    st.rerun()


def display_files():
    st.subheader("Uploaded Files")

    # Get the list of files and their statuses from the server
    headers = {'Authorization': 'Bearer ' + st.session_state['token']}
    response = requests.get('https://1d1d-116-73-245-216.ngrok-free.app/list_uploaded_files', headers=headers)
    if response.status_code == 200:
        files_data = response.json().get('files', [])
        if st.button("Refresh", key="refresh_files"):
            st.rerun()
        if files_data:
            # Only keep the latest entry per filename
            unique_files = {}
            for file_info in files_data:
                filename = file_info['filename']
                if filename not in unique_files:
                    unique_files[filename] = file_info
            # Now display the files
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

    # Get the list of files from the server
    headers = {'Authorization': 'Bearer ' + st.session_state['token']}
    response = requests.get('https://1d1d-116-73-245-216.ngrok-free.app/list_uploaded_files', headers=headers)
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

                # Add a delete button with a unique key
                if col3.button("Delete", key=f"delete_{upload_id}"):
                    # Send delete request to server
                    data = {'upload_id': upload_id}
                    headers = {
                        'Authorization': 'Bearer ' + st.session_state['token'],
                        'Content-Type': 'application/json'
                    }
                    delete_response = requests.post('https://1d1d-116-73-245-216.ngrok-free.app/delete_upload', headers=headers, json=data)
                    if delete_response.status_code == 200:
                        st.success(f"Deleted {filename}")
                        st.rerun()
                    else:
                        # Attempt to parse JSON response
                        try:
                            error_message = delete_response.json().get('message', 'Unknown error')
                        except (json.JSONDecodeError, requests.exceptions.JSONDecodeError):
                            # If response is not JSON, use the text content
                            error_message = delete_response.text or 'Unknown error'
                        st.error(f"Failed to delete {filename}: {error_message}")
        else:
            st.write("No files uploaded yet.")
    else:
        st.error("Failed to fetch files.")

def generate_response(prompt, options):
    headers = {'Authorization': 'Bearer ' + st.session_state['token']}
    payload = {
        "query": prompt,
        "files": options
    }
    try:
        run_response = requests.post('https://1d1d-116-73-245-216.ngrok-free.app/run_excel_agent', 
                                   headers=headers, 
                                   json=payload,
                                   timeout=180)  # 3 minutes timeout
        if run_response.status_code == 200:
            final_answer = run_response.json().get('answer', '')
            return final_answer
        else:
            return f"Error: Server returned status code {run_response.status_code}"
    except requests.Timeout:
        return "Error: Request timed out. The server is taking too long to respond."
    except requests.RequestException as e:
        return f"Error: Connection failed - {str(e)}"

def main():
    if st.session_state['token']:
      
        # Create a header with logout button at the top right
        header_cols = st.columns([8, 1])
        with header_cols[0]:
            st.title("DataDash - AI Powered Business Insights")
   
        with header_cols[1]:
            st.write("")  # Placeholder
            if st.button("Logout"):
                logout()

        # Create a sidebar for navigation
        with st.sidebar:
 
            
            # Create a styled option menu in the sidebar
            page = option_menu(
            "Menu Options", 
            ["Home", "Data Insights"],  
            icons=['house', 'file-text'], 
            menu_icon="list",
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "	#ffffff", "font-size": "20px"}, 
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

            # You can add more visual elements to the sidebar for aesthetics
            st.markdown("""
            <style>
            .sidebar .sidebar-content {
                background-image: linear-gradient(#ff2b2b,#ff2b2b);
                color: white;
            }
            </style>
            """, unsafe_allow_html=True)

        # Display the selected page
        if page == "Home":
            # Keep the Upload and Uploaded tabs as they are
            tab1, tab2, tab3 = st.tabs(["Upload", "Uploaded", "Status"])

            with tab1:
                # Update the Dropzone HTML to include the JWT token
                token = st.session_state['token']
                dropzone_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <!-- Include CSS -->
            <style>
                /* Hardcoded colors */
                :root {{
                    --primary-color: #BB86FC;
                    --background-color: #F0F2F6;
                    --text-color: #333333;
                    --font: "Source Sans Pro", sans-serif;
                }}
                /* Dark mode colors */
                
                

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

                /* Scrollbar styling */
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
            <form action="https://1d1d-116-73-245-216.ngrok-free.app/upload" class="dropzone" id="fileDropzone">
                <div class="dz-message">
                    Drag and drop files here or click to upload.
                </div>
            </form>
            <script>
                // Your JWT token
                const jwtToken = "{token}";

                Dropzone.options.fileDropzone = {{
                    paramName: "file",
                    maxFilesize: 1024, // Maximum file size in MB
                    uploadMultiple: false, // Disable multiple files upload at once
                    parallelUploads: 2, // Process one file at a time
                    timeout: 300000, // Timeout in milliseconds
                    clickable: true, // Allow clicking to open file dialog
                    autoProcessQueue: true, // Process files automatically
                    init: function() {{
                        this.on("sending", function(file, xhr, formData) {{
                            // Add JWT to the Authorization header for upload requests
                            xhr.setRequestHeader("Authorization", "Bearer " + jwtToken);
                        }});

                        this.on("addedfile", function(file) {{
                            // Create a delete icon
                            let deleteIcon = document.createElement("img");
                            deleteIcon.src = "https://cdn2.iconfinder.com/data/icons/user-interface-presicon-line/64/cross-512.png";
                            deleteIcon.className = "delete-icon";

                            // Append the delete icon to the file preview
                            file.previewElement.appendChild(deleteIcon);

                            // Handle click event on the delete icon
                            deleteIcon.addEventListener("click", function(e) {{
                                e.preventDefault(); // Prevent default behavior
                                e.stopPropagation(); // Stop propagation

                                // Remove the file preview from the Dropzone
                                this.removeFile(file);

                                // Send a POST request to the server to delete the file
                                fetch('https://1d1d-116-73-245-216.ngrok-free.app/delete', {{
                                    method: 'POST',
                                    headers: {{
                                        'Content-Type': 'application/json',
                                        'Authorization': 'Bearer ' + jwtToken // Add JWT to the delete request
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
                            }}.bind(this)); // Bind 'this' to Dropzone instance
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
            if "messages" not in st.session_state:
                st.session_state.messages = []

            # Create a container for chat history
            chat_container = st.container()

            # Fetch user-specific files when the page loads (inside the main() function, after confirming user is logged in)
            headers = {'Authorization': 'Bearer ' + st.session_state['token']}
            response = requests.get('https://1d1d-116-73-245-216.ngrok-free.app/get_user_files', headers=headers)
            if response.status_code == 200:
                files_data = response.json().get('files', [])
                options = st.multiselect(
                    "Select files to query",
                    files_data,
                    []
                )
            else:
                st.error("Failed to fetch user files.")
                options = []

            

            # Display chat input and clear button
            col1, col2 = st.columns([6, 1])
            with col1:
                prompt = st.chat_input("Type your message here...")
            with col2:
                if st.button("Clear Chat"):
                    st.session_state.messages = []
                    st.rerun()

            
            # Display chat history and handle new messages
            with chat_container:
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        if message["role"] == "assistant":
                            st.markdown(message["content"], unsafe_allow_html=True)
                        else:
                            st.write(message["content"])

                if prompt:
                    # Display user message
                    with st.chat_message("user"):
                        st.write(prompt)
                    st.session_state.messages.append({"role": "user", "content": prompt})
                 
                    # Generate assistant's response
                    with st.spinner("Thinking..."):
                        response = generate_response(prompt, options)  # Generate Markdown content here
                    st.session_state.messages.append({"role": "assistant", "content": response})

                    with st.chat_message("assistant"):
                        # Display response as Markdown
                        message_placeholder = st.empty()
                        for i in range(len(response)):
                            message_placeholder.markdown(
                                f"<div class='assistant-message'>🤖 {response[:i+1]}</div>",
                                unsafe_allow_html=True
                            )
                            time.sleep(0.00000000000002)

            # Automatically scroll to the bottom
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
        # User is not logged in
        st.title("DataDash - AI Powered Business Insights")
        st.write("Please login or sign up.")
        # Add CSS for tabs styling
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
            background-color: 		#262730 !important;
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
