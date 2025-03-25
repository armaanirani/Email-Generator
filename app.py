import streamlit as st
import os
import io
from openai import OpenAI
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import PyPDF2
from docx import Document
import pandas as pd
from datetime import datetime

# Load environment variables
load_dotenv()

# Set up page configuration
st.set_page_config(
    page_title="AI Email Generator",
    page_icon="✉️",
    layout="centered"
)

# Initialize OpenAI client
def initialize_openai_client(api_key):
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"Error initializing OpenAI client: {str(e)}")
        return None

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'favorites' not in st.session_state:
    st.session_state.favorites = []

# File processing functions (keep your existing functions here)
def extract_text_from_file(file):
    try:
        file_type = file.name.split('.')[-1].lower()
        
        if file_type == 'pdf':
            return extract_text_from_pdf(file)
        elif file_type == 'docx':
            return extract_text_from_docx(file)
        elif file_type in ['xlsx', 'xls']:
            return extract_text_from_excel(file)
        elif file_type == 'txt':
            return file.read().decode('utf-8')
        else:
            return f"[File content not extracted: Unsupported format ({file_type})]"
            
    except Exception as e:
        return f"[Error processing file {file.name}: {str(e)}]"

def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(file):
    doc = Document(io.BytesIO(file.read()))
    return '\n'.join([para.text for para in doc.paragraphs])

def extract_text_from_excel(file):
    df = pd.read_excel(file)
    return df.to_string()

# PDF generation function
def generate_pdf(content):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y_position = height - 40
    line_height = 14
    
    text = c.beginText(40, y_position)
    text.setFont("Courier", 12)
    
    for line in content.split('\n'):
        if y_position < 40:
            c.drawText(text)
            c.showPage()
            y_position = height - 40
            text = c.beginText(40, y_position)
            text.setFont("Courier", 12)
        
        text.textLine(line)
        y_position -= line_height
    
    c.drawText(text)
    c.save()
    buffer.seek(0)
    return buffer

# Sidebar for API key input
with st.sidebar:
    st.title("Settings")
    api_key_input = st.text_input("Enter OpenAI API Key:", type="password")
    st.markdown("[Get OpenAI API Key](https://platform.openai.com/api-keys)")

# Get API key from .env or user input
api_key = api_key_input or os.getenv("OPENAI_API_KEY")

# Create tabs for main interface
tab1, tab2 = st.tabs(["📧 Email Generator", "📚 History & Favorites"])

with tab1:
    # Main app interface
    st.title("✉️ AI Email Generator")
    st.write("Customize your email using the options below:")

    # Email configuration options
    with st.expander("⚙️ Email Configuration", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            tone = st.selectbox(
                "Select Tone:",
                ["Professional", "Friendly", "Casual", "Persuasive", "Sympathetic"]
            )
            email_length = st.selectbox(
                "Email Length:",
                ["Short", "Medium", "Detailed"]
            )
        with col2:
            writing_style = st.selectbox(
                "Writing Style:",
                ["Direct", "Descriptive", "Storytelling", "Technical"]
            )
            language = st.selectbox(
                "Language:",
                ["English", "Spanish", "French", "German", "Chinese"]
            )

    # User inputs
    with st.form("email_inputs"):
        col1, col2 = st.columns(2)
        with col1:
            user_name = st.text_input("Your Name:")
            user_role = st.text_input("Your Role/Position:")
        with col2:
            recipient_name = st.text_input("Recipient's Name:")
            recipient_role = st.text_input("Recipient's Role/Position:")

        email_purpose = st.text_area("Purpose of the Email:")
        background_info = st.text_area("Background Information:")
        special_instructions = st.text_area("Any Special Instructions:")
        
        # File attachment section
        uploaded_files = st.file_uploader(
            "Attach Files (will be referenced in email):",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'xlsx', 'jpg', 'png']
        )

        generate_button = st.form_submit_button("✨ Generate Email")

    # Store uploaded files in session state
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
    elif 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []

    # Email generation function
    def generate_email(prompt):
        try:
            client = initialize_openai_client(api_key)
            if not client:
                return None
                
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"Error generating email: {str(e)}")
            return None

    # Generate and display email
    if generate_button:
        if not api_key:
            st.error("Please enter your OpenAI API key in the sidebar or add it to your .env file!")
        else:
            with st.spinner("Generating your perfect email..."):
                # Process uploaded files
                file_contents = []
                if st.session_state.uploaded_files:
                    for file in st.session_state.uploaded_files:
                        content = extract_text_from_file(file)
                        file_contents.append(f"=== Content from {file.name} ===\n{content}\n")
                
                # Combine file contents with truncation
                combined_content = '\n'.join(file_contents)
                if len(combined_content) > 3000:  # Keep within context window
                    combined_content = combined_content[:3000] + "\n[Content truncated due to length]"
                
                # Build enhanced prompt
                prompt = f"""
                Compose a {tone.lower()} email in {language} with these specifications:
                
                - Sender: {user_name} ({user_role})
                - Recipient: {recipient_name} ({recipient_role})
                - Purpose: {email_purpose}
                - Background: {background_info}
                - Special instructions: {special_instructions}
                
                Incorporate relevant information from these attached files:
                {combined_content if combined_content else "No file content available"}
                
                Structure:
                1. Clear subject line
                2. Appropriate greeting
                3. Body with references to attached files where relevant
                4. Professional closing
                5. Mention of attachments
                
                Make sure to:
                - Maintain {writing_style.lower()} style
                - Keep length {email_length.lower()}
                - Highlight key points from file content
                - Use proper business email formatting
                """

                generated_email = generate_email(prompt)
                if generated_email:
                    email_record = {
                        "content": generated_email,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "favorite": False,
                        "metadata": {
                            "tone": tone,
                            "recipient": recipient_name,
                            "purpose": email_purpose[:50]
                        }
                    }
                    st.session_state.history.append(email_record)
                    # Keep only last 10 history items
                    if len(st.session_state.history) > 10:
                        st.session_state.history = st.session_state.history[-10:]
                    st.session_state.generated_email = generated_email
                    st.session_state.edit_mode = False
                    st.rerun()

    if 'generated_email' in st.session_state:
        st.success("Email generated successfully!")

        # Show attached files
        if st.session_state.uploaded_files:
            st.subheader("📎 Attached Files")
            for file in st.session_state.uploaded_files:
                st.write(f"- {file.name} ({file.size//1024} KB)")

        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = False

        # Email display/edit area
        if st.session_state.edit_mode:
            edited_email = st.text_area(
                "Edit your email:", 
                value=st.session_state.generated_email,
                height=400,
                key="email_editor"
            )
            st.session_state.generated_email = edited_email
        else:
            # Use code block with copy button
            st.code(st.session_state.generated_email, language="text")

        # Action buttons row
        col1, col2, col3, col4 = st.columns([1,1,1,1])
        
        with col1:
            if st.session_state.edit_mode:
                if st.button("💾 Save Changes", use_container_width=True):
                    st.session_state.edit_mode = False
                    st.rerun()
            else:
                if st.button("✏️ Edit Email", use_container_width=True):
                    st.session_state.edit_mode = True
                    st.rerun()
        
        with col2:
            st.download_button(
                label="⬇️ TXT",
                data=st.session_state.generated_email,
                file_name="generated_email.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col3:
            pdf_buffer = generate_pdf(st.session_state.generated_email)
            st.download_button(
                label="⬇️ PDF",
                data=pdf_buffer,
                file_name="generated_email.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        
        with col4:
            current_email_index = next((i for i, email in enumerate(st.session_state.history) 
                                    if email['content'] == st.session_state.generated_email), None)
            if current_email_index is not None:
                is_favorite = st.session_state.history[current_email_index]['favorite']
                fav_label = "❤️ Remove from Favorites" if is_favorite else "♡ Add to Favorites"
                if st.button(fav_label, 
                            use_container_width=True,
                            key=f"fav_toggle_{current_email_index}"):
                    st.session_state.history[current_email_index]['favorite'] = not is_favorite
                    st.rerun()

with tab2:
    st.title("📚 Email History & Favorites")
    
    # History Section
    st.header("📜 Email History")
    if not st.session_state.history:
        st.info("No email history yet. Generate some emails to see them here!")
    else:
        # Reverse history to show newest first
        reversed_history = list(reversed(st.session_state.history))
        
        for idx, email in enumerate(reversed_history):
            with st.expander(f"{email['timestamp']} - {email['metadata']['recipient']} - {email['metadata']['purpose']}"):
                col1, col2 = st.columns([4,1])
                with col1:
                    st.write(f"**Tone:** {email['metadata']['tone']}")
                    st.code(email['content'], language="text")
                with col2:
                    # Favorite toggle
                    is_favorite = email['favorite']
                    fav_label = "❤️ Remove Favorite" if is_favorite else "♡ Add Favorite"
                    if st.button(fav_label, key=f"hist_fav_{idx}"):
                        # Find the original email in history (not reversed)
                        original_idx = len(st.session_state.history) - 1 - idx
                        st.session_state.history[original_idx]['favorite'] = not is_favorite
                        st.rerun()
                    
                    # Load button
                    if st.button("📝 Load", key=f"hist_load_{idx}"):
                        st.session_state.generated_email = email['content']
                        st.session_state.edit_mode = False
                        # Switch to the first tab
                        st.session_state.current_tab = "📧 Email Generator"
                        st.rerun()
    
    # Favorites Section
    st.header("⭐ Favorite Emails")
    favorite_emails = [email for email in st.session_state.history if email['favorite']]
    if not favorite_emails:
        st.info("No favorite emails yet. Add some by clicking the heart icon!")
    else:
        # Reverse favorites to show newest first
        reversed_favorites = list(reversed(favorite_emails))
        
        for idx, email in enumerate(reversed_favorites):
            with st.expander(f"{email['timestamp']} - {email['metadata']['recipient']} - {email['metadata']['purpose']}"):
                col1, col2 = st.columns([4,1])
                with col1:
                    st.write(f"**Tone:** {email['metadata']['tone']}")
                    st.code(email['content'], language="text")
                with col2:
                    # Remove favorite button
                    if st.button("❤️ Remove Favorite", key=f"fav_remove_{idx}"):
                        # Find the original email in history (not reversed)
                        original_idx = len(st.session_state.history) - 1 - [i for i, e in enumerate(reversed_history) if e['timestamp'] == email['timestamp']][0]
                        st.session_state.history[original_idx]['favorite'] = False
                        st.rerun()
                    
                    # Load button
                    if st.button("📝 Load", key=f"fav_load_{idx}"):
                        st.session_state.generated_email = email['content']
                        st.session_state.edit_mode = False
                        # Switch to the first tab
                        st.session_state.current_tab = "📧 Email Generator"
                        st.rerun()