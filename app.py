import streamlit as st
import os
import io
import time
from openai import OpenAI
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import PyPDF2
from docx import Document
import pandas as pd
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import base64

# --- Configuration ---
load_dotenv()  # Load environment variables

# Set up page configuration
st.set_page_config(
    page_title="AI Email Generator",
    page_icon="✉️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Constants ---
DEFAULT_MODEL = "gpt-4o-mini"  # Updated default model
MODEL_OPTIONS = ["gpt-4o", "gpt-4o-mini", "o1-mini", "o3-mini"]  # Current model options
MAX_HISTORY_ITEMS = 20  # Maximum number of history items to keep
MAX_FILE_SIZE_MB = 5  # Maximum file size for attachments in MB
MAX_CONTENT_LENGTH = 3000  # Maximum context length for file content
MAX_RETRIES = 3  # Maximum API retry attempts

# Define email presets with templates and metadata
EMAIL_PRESETS = {
    "Job Application": {
        "tone": "Professional",
        "purpose": "Applying for a job position",
        "template": """Subject: Application for [Position Name] at [Company Name]

Dear [Hiring Manager's Name],

I am excited to apply for the [Position Name] role at [Company Name]. With my background in [Relevant Field/Experience], I am confident in my ability to contribute effectively to your team.

In my current role at [Current Company], I have [describe key achievement or responsibility]. This experience has equipped me with [specific skills] that align well with the requirements for this position.

I am particularly drawn to [Company Name] because of [specific reason - company values, projects, etc.]. I would welcome the opportunity to bring my [specific skills] to your team.

Please find my resume attached for your review. I would appreciate the chance to discuss how my skills and experiences align with your needs. I am available at [your phone number] or [your email] at your convenience.

Thank you for your time and consideration. I look forward to the possibility of contributing to your team.

Best regards,
[Your Name]"""
    },
    "Follow-Up Email": {
        "tone": "Professional",
        "purpose": "Following up after a meeting or application",
        "template": """Subject: Following Up on [Meeting/Application Topic]

Dear [Recipient's Name],

I hope this email finds you well. I wanted to follow up regarding our recent [meeting/conversation] about [topic] on [date]. 

[If applicable: Thank you again for taking the time to [discuss/meet about] [topic]. I found our conversation particularly valuable because [specific reason].]

[If waiting for response: I understand you're busy, but I wanted to check if there have been any updates regarding [specific question or next steps].]

Please don't hesitate to let me know if you need any additional information from my side. I'm happy to provide further details or clarify anything about [subject].

Looking forward to hearing from you.

Best regards,
[Your Name]"""
    },
    "Thank You Note": {
        "tone": "Friendly",
        "purpose": "Expressing gratitude after an interview or favor",
        "template": """Subject: Thank You for [Specific Reason]

Dear [Recipient's Name],

I wanted to take a moment to sincerely thank you for [specific reason - interview, help, gift, etc.]. I truly appreciate the time and effort you took to [specific action].

[For interviews: I particularly enjoyed learning about [something specific from the conversation]. Our discussion about [topic] reinforced my excitement about the opportunity to join [Company Name].]

[If appropriate: Please don't hesitate to let me know if there's ever anything I can do to return the favor.]

Thanks again for your [kindness/guidance/support]. It means a great deal to me.

Warm regards,
[Your Name]"""
    },
    "Sales Pitch": {
        "tone": "Persuasive",
        "purpose": "Introducing a product or service to potential clients",
        "template": """Subject: [Product/Service] to Help You [Solve Problem]

Dear [Recipient's Name],

I hope you're doing well. I'm reaching out because I believe [Company Name]'s [Product/Service] could help you [solve specific problem or achieve specific goal].

Many [industry] professionals like yourself are facing challenges with [specific pain point]. Our solution helps by [key benefit 1], [key benefit 2], and [key benefit 3].

For example, we recently helped [Client Name] achieve [specific result] within [timeframe]. They were able to [specific outcome] while reducing [pain point] by [percentage].

I'd love to schedule a quick call to discuss how we might be able to help you with [specific challenge]. Would [date/time] or [date/time] work for you?

In the meantime, I've attached [relevant materials] that provide more details about our solution.

Looking forward to the possibility of working together.

Best regards,
[Your Name]
[Your Position]
[Your Company]"""
    },
    "Networking Request": {
        "tone": "Professional",
        "purpose": "Requesting an informational interview or connection",
        "template": """Subject: Request for [Informational Interview/Advice]

Dear [Recipient's Name],

I hope this message finds you well. My name is [Your Name], and I'm [your current position/student status] with a strong interest in [field/industry].

I've been following your work at [Company/Organization] and particularly admire [specific aspect of their work]. I would greatly appreciate the opportunity to learn more about your experiences and insights in [specific area].

Would you be available for a brief [15-20 minute] conversation in the coming weeks? I'm happy to accommodate your schedule and can meet in person or virtually, whichever is most convenient for you.

I completely understand if you're unable to spare the time, but any advice you could share would be invaluable as I [your current goal - navigate my career path, learn about the industry, etc.].

Thank you for considering this request. I look forward to the possibility of connecting.

Best regards,
[Your Name]
[Your Contact Information]"""
    }
}

# --- Helper Functions ---

def initialize_openai_client():
    """Initialize and return OpenAI client using API key from .env"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY not found in .env file")
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"Error initializing OpenAI client: {str(e)}")
        return None

def validate_file(file):
    """Validate uploaded file size and type."""
    valid_types = ['pdf', 'docx', 'xlsx', 'txt', 'jpg', 'png', 'jpeg']
    file_type = file.name.split('.')[-1].lower()
    
    if file_type not in valid_types:
        raise ValueError(f"Unsupported file type: {file_type}")
    if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(f"File size exceeds {MAX_FILE_SIZE_MB}MB limit")
    return True

def extract_text_from_file(file):
    """Extract text content from various file types with error handling."""
    try:
        validate_file(file)
        file_type = file.name.split('.')[-1].lower()
        
        if file_type == 'pdf':
            return extract_text_from_pdf(file)
        elif file_type == 'docx':
            return extract_text_from_docx(file)
        elif file_type in ['xlsx', 'xls']:
            return extract_text_from_excel(file)
        elif file_type == 'txt':
            return file.read().decode('utf-8')
        elif file_type in ['jpg', 'png', 'jpeg']:
            return "[Image content - description not extracted]"
        else:
            return f"[Unsupported file format: {file_type}]"
    except Exception as e:
        return f"[Error processing {file.name}: {str(e)}]"

def extract_text_from_pdf(file):
    """Extract text from PDF files."""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"PDF extraction error: {str(e)}")

def extract_text_from_docx(file):
    """Extract text from Word documents."""
    try:
        doc = Document(io.BytesIO(file.read()))
        return '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception as e:
        raise Exception(f"DOCX extraction error: {str(e)}")

def extract_text_from_excel(file):
    """Extract text from Excel files."""
    try:
        df = pd.read_excel(file)
        return df.to_string()
    except Exception as e:
        raise Exception(f"Excel extraction error: {str(e)}")

# def generate_pdf(content):
#     """Generate PDF from email content with proper formatting."""
#     buffer = io.BytesIO()
#     try:
#         c = canvas.Canvas(buffer, pagesize=letter)
#         width, height = letter
#         y_position = height - 40
#         line_height = 14
        
#         text = c.beginText(40, y_position)
#         text.setFont("Courier", 12)
        
#         for line in content.split('\n'):
#             if y_position < 40:
#                 c.drawText(text)
#                 c.showPage()
#                 y_position = height - 40
#                 text = c.beginText(40, y_position)
#                 text.setFont("Courier", 12)
            
#             text.textLine(line)
#             y_position -= line_height
        
#         c.drawText(text)
#         c.save()
#         buffer.seek(0)
#         return buffer
#     except Exception as e:
#         st.error(f"Error generating PDF: {str(e)}")
#         return None

def generate_pdf(content, title="Generated Email"):
    """Generate PDF from email content with proper formatting."""
    buffer = io.BytesIO()
    try:
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        flowables = []
        
        # Add title
        flowables.append(Paragraph(title, styles['Title']))
        flowables.append(Spacer(1, 12))
        
        # Process content
        for line in content.split('\n'):
            if line.strip():
                if line.startswith('Subject:'):
                    flowables.append(Paragraph(f"<b>{line}</b>", styles['Heading2']))
                elif line.startswith('Dear'):
                    flowables.append(Paragraph(line, styles['Heading3']))
                elif any(line.startswith(prefix) for prefix in ['Best regards,', 'Sincerely,', 'Regards,']):
                    flowables.append(Paragraph(line, styles['Heading3']))
                else:
                    flowables.append(Paragraph(line, styles['BodyText']))
                
                flowables.append(Spacer(1, 6))
        
        doc.build(flowables)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None

def create_download_link_pdf(pdf_bytes, filename, link_text):
    """Create a download link for PDF content"""
    b64 = base64.b64encode(pdf_bytes.getvalue()).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

def create_download_link_txt(text_content, filename, link_text):
    """Create a download link for text content"""
    b64 = base64.b64encode(text_content.encode()).decode()
    href = f'<a href="data:text/plain;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

def build_email_prompt(params):
    """Construct the prompt for email generation."""
    file_contents = []
    if params.get('uploaded_files'):
        with st.spinner("Processing attachments..."):
            for file in params['uploaded_files']:
                content = extract_text_from_file(file)
                file_contents.append(f"=== Content from {file.name} ===\n{content}\n")
    
    combined_content = '\n'.join(file_contents)
    if len(combined_content) > MAX_CONTENT_LENGTH:
        combined_content = combined_content[:MAX_CONTENT_LENGTH] + "\n[Content truncated]"

    return f"""
    Compose a {params['tone'].lower()} email in {params['language']} with these specifications:
    
    - Sender: {params['user_name']} ({params['user_role']})
    - Recipient: {params['recipient_name']} ({params['recipient_role']})
    - Purpose: {params['email_purpose']}
    - Background: {params['background_info']}
    - Special instructions: {params['special_instructions']}
    
    {f"Incorporate relevant information from these attached files:\n{combined_content}" if combined_content else "No file content available"}
    
    Structure:
    1. Clear subject line
    2. Appropriate greeting
    3. Well-structured body
    4. Professional closing
    5. Mention of attachments if applicable
    
    Style Guidelines:
    - Maintain {params['writing_style'].lower()} style
    - Keep length {params['email_length'].lower()}
    - Use proper business email formatting
    - Highlight key points from file content when relevant
    """

def generate_email_with_retry(prompt, max_retries=MAX_RETRIES):
    """Generate email with retry logic for API failures."""
    client = initialize_openai_client(st.session_state.api_key)
    if not client:
        return None
        
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=st.session_state.selected_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt == max_retries - 1:
                st.error(f"Failed after {max_retries} attempts: {str(e)}")
                raise e
            wait_time = 1 * (attempt + 1)
            time.sleep(wait_time)

def remove_attachment(file_name):
    """Remove an attachment from the uploaded files"""
    st.session_state.uploaded_files = [
        f for f in st.session_state.uploaded_files 
        if f.name != file_name
    ]

# --- Session State Initialization ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'selected_preset' not in st.session_state:
    st.session_state.selected_preset = None
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = DEFAULT_MODEL

# --- Sidebar Configuration ---
with st.sidebar:
    st.title("Settings")

    # Model selection
    st.session_state.selected_model = st.selectbox(
        "Select AI Model:",
        MODEL_OPTIONS,
        index=MODEL_OPTIONS.index(DEFAULT_MODEL),
        help="More powerful models may produce better results but cost more"
    )
    
    st.markdown("---")
    st.caption("Note: API key is loaded from .env file")

# --- Main Application Tabs ---
tab1, tab2 = st.tabs(["📧 Email Generator", "📚 History & Favorites"])

with tab1:
    # --- Email Generator Interface ---
    st.title("✉️ AI Email Generator")
    st.caption("Create professional emails with AI assistance")
    
    # --- Preset Selection Section ---
    with st.expander("📁 Email Presets", expanded=False):
        preset_col1, preset_col2 = st.columns([3, 1])
        with preset_col1:
            selected_preset_name = st.selectbox(
                "Choose a template:",
                ["Custom Email"] + list(EMAIL_PRESETS.keys()),
                index=0,
                help="Select a template to get started quickly",
                key="preset_selector"
            )
        with preset_col2:
            if selected_preset_name != "Custom Email":
                if st.button("Load Preset", key="load_preset_button", help="Load this template"):
                    st.session_state.selected_preset = EMAIL_PRESETS[selected_preset_name]
                    st.rerun()
        
        # Clear preset button with immediate effect
        if st.session_state.get('selected_preset'):
            st.info(f"Loaded preset: {selected_preset_name}")
            if st.button("Clear Preset", key="clear_preset_button", help="Return to custom email"):
                st.session_state.selected_preset = None
                st.rerun()

    # --- Email Configuration ---
    with st.expander("⚙️ Email Configuration", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            tone = st.selectbox(
                "Select Tone:",
                ["Professional", "Friendly", "Casual", "Persuasive", "Sympathetic"],
                index=["Professional", "Friendly", "Casual", "Persuasive", "Sympathetic"].index(
                    st.session_state.selected_preset["tone"] if st.session_state.selected_preset else "Professional"
                ),
                help="Set the overall tone of the email"
            )
            email_length = st.selectbox(
                "Email Length:",
                ["Short", "Medium", "Detailed"],
                help="Control the verbosity of the generated email"
            )
        with col2:
            writing_style = st.selectbox(
                "Writing Style:",
                ["Direct", "Descriptive", "Storytelling", "Technical"],
                help="Choose the writing approach"
            )
            language = st.selectbox(
                "Language:",
                ["English", "Spanish", "French", "German", "Chinese"],
                help="Select the output language"
            )

    # --- Email Content Form ---
    with st.form("email_inputs", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            user_name = st.text_input("Your Name:", help="Your full name")
            user_role = st.text_input("Your Role/Position:", help="Your job title or position")
        with col2:
            recipient_name = st.text_input("Recipient's Name:", help="Who will receive this email")
            recipient_role = st.text_input("Recipient's Role/Position:", help="Their job title or position")

        email_purpose = st.text_area(
            "Purpose of the Email:",
            value=st.session_state.selected_preset["purpose"] if st.session_state.selected_preset else "",
            help="Clearly state what this email is about",
            max_chars=200
        )
        st.caption(f"{len(email_purpose)}/200 characters")
        
        background_info = st.text_area(
            "Background Information:",
            help="Any relevant context the AI should know",
            max_chars=500
        )
        st.caption(f"{len(background_info)}/500 characters")
        
        special_instructions = st.text_area(
            "Any Special Instructions:",
            help="Specific requests for how the email should be written",
            max_chars=300
        )
        st.caption(f"{len(special_instructions)}/300 characters")
        
        # File attachment section
        uploaded_files = st.file_uploader(
            "Attach Files (will be referenced in email):",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'xlsx', 'txt', 'jpg', 'png', 'jpeg'],
            help=f"Maximum file size: {MAX_FILE_SIZE_MB}MB each",
            key="file_uploader"
        )

        generate_button = st.form_submit_button(
            "✨ Generate Email",
            help="Generate email using the provided information"
        )

    # Store uploaded files in session state
    if uploaded_files:
        invalid_files = [f for f in uploaded_files if not validate_file(f)]
        if invalid_files:
            st.warning(f"Skipped {len(invalid_files)} invalid files (type or size)")
        st.session_state.uploaded_files = [f for f in uploaded_files if validate_file(f)]

    # Display current attachments with remove buttons (outside the form)
    if st.session_state.uploaded_files:
        st.write("**Current Attachments:**")
        for file in st.session_state.uploaded_files:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"- {file.name} ({file.size//1024} KB)")
            with col2:
                if st.button("❌ Remove", key=f"remove_{file.name}"):
                    st.session_state.uploaded_files = [
                        f for f in st.session_state.uploaded_files 
                        if f.name != file.name
                    ]
                    st.rerun()

    # --- Email Generation Logic ---
    if generate_button:
        with st.spinner("Generating your email..."):
            try:
                client = initialize_openai_client()
                if not client:
                    st.error("Failed to initialize OpenAI client. Please check your .env file.")
                    st.stop()

                prompt = build_email_prompt({
                    'tone': tone,
                    'language': language,
                    'user_name': user_name,
                    'user_role': user_role,
                    'recipient_name': recipient_name,
                    'recipient_role': recipient_role,
                    'email_purpose': email_purpose,
                    'background_info': background_info,
                    'special_instructions': special_instructions,
                    'writing_style': writing_style,
                    'email_length': email_length,
                    'uploaded_files': st.session_state.uploaded_files
                })
                
                response = client.chat.completions.create(
                    model=st.session_state.selected_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1500
                )
                generated_email = response.choices[0].message.content.strip()
                    
                if generated_email:
                    # Save to history
                    email_record = {
                        "content": generated_email,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "favorite": False,
                        "metadata": {
                            "tone": tone,
                            "recipient": recipient_name,
                            "purpose": email_purpose[:50],
                            "preset": selected_preset_name if selected_preset_name != "Custom Email" else None
                        }
                    }
                    st.session_state.history.append(email_record)
                        
                    # Maintain history size limit
                    if len(st.session_state.history) > MAX_HISTORY_ITEMS:
                        st.session_state.history = st.session_state.history[-MAX_HISTORY_ITEMS:]
                            
                    st.session_state.generated_email = generated_email
                    st.session_state.edit_mode = False
                    st.session_state.selected_preset = None
                    st.rerun()
                        
            except Exception as e:
                st.error(f"Error generating email: {str(e)}")

    # --- Generated Email Display ---
    if 'generated_email' in st.session_state:
        st.success("Email generated successfully!")
        
        # Show attachments if any
        if st.session_state.uploaded_files:
            with st.expander("📎 Attachments", expanded=False):
                for file in st.session_state.uploaded_files:
                    st.write(f"- {file.name} ({file.size//1024} KB)")

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
            st.code(st.session_state.generated_email, language="text")

        # Action buttons
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
            if st.button("📝 Save as txt", key="save_email_text"):
                txt_filename = f"email_to_{recipient_name.replace(' ', '_')}.txt"
                st.markdown(
                    create_download_link_txt(
                        st.session_state.generated_email,
                        filename=txt_filename,
                        link_text="📥 Download as Text"
                    ),
                    unsafe_allow_html=True
                )
        
        with col3:
            if st.button("📄 Save as PDF", key="save_email_pdf"):
                
                # Generate the PDF
                pdf_buffer = generate_pdf(
                    st.session_state.generated_email,
                    title=f"Email to {recipient_name}"
                )
                
                # Create the download link
                if pdf_buffer:
                    st.markdown(
                        create_download_link_pdf(
                            pdf_buffer,
                            filename=f"email_to_{recipient_name.replace(' ', '_')}.pdf",
                            link_text="📥 Download as PDF"
                        ),
                        unsafe_allow_html=True
                    )
        
        with col4:
            current_email_index = next(
                (i for i, email in enumerate(st.session_state.history) 
                if email['content'] == st.session_state.generated_email
            ), None)
            
            if current_email_index is not None:
                is_favorite = st.session_state.history[current_email_index]['favorite']
                fav_label = "❤️ Remove Favorite" if is_favorite else "♡ Add Favorite"
                if st.button(
                    fav_label, 
                    use_container_width=True,
                    key=f"fav_toggle_{current_email_index}"
                ):
                    st.session_state.history[current_email_index]['favorite'] = not is_favorite
                    st.rerun()

with tab2:
    # --- History & Favorites Interface ---
    st.title("📚 Email History & Favorites")
    
    # Clear All History Button
    if st.session_state.history:
        if st.button("🗑️ Clear All History", type="primary"):
            st.session_state.history = []
            st.session_state.favorites = []
            st.rerun()
    
    # History Section
    st.header("📜 Email History")
    if not st.session_state.history:
        st.info("No email history yet. Generate some emails to see them here!")
    else:
        for idx, email in enumerate(reversed(st.session_state.history)):
            with st.expander(
                f"{email['timestamp']} - {email['metadata']['recipient']} - {email['metadata']['purpose']}",
                expanded=False
            ):
                col1, col2 = st.columns([4,1])
                with col1:
                    st.write(f"**Tone:** {email['metadata']['tone']}")
                    if email['metadata'].get('preset'):
                        st.write(f"**Template:** {email['metadata']['preset']}")
                    st.code(email['content'], language="text")
                with col2:
                    # Favorite toggle
                    is_favorite = email['favorite']
                    fav_label = "❤️ Remove" if is_favorite else "♡ Add"
                    if st.button(fav_label, key=f"hist_fav_{idx}"):
                        original_idx = len(st.session_state.history) - 1 - idx
                        st.session_state.history[original_idx]['favorite'] = not is_favorite
                        st.rerun()
                    
                    # Load button
                    if st.button("📝 Load", key=f"hist_load_{idx}"):
                        st.session_state.generated_email = email['content']
                        st.session_state.edit_mode = False
                        st.session_state.current_tab = "📧 Email Generator"
                        st.rerun()
                    
                    # Delete button
                    if st.button("🗑️ Delete", key=f"hist_delete_{idx}"):
                        original_idx = len(st.session_state.history) - 1 - idx
                        st.session_state.history.pop(original_idx)
                        st.rerun()
    
    # Favorites Section
    st.header("⭐ Favorite Emails")
    favorite_emails = [email for email in st.session_state.history if email['favorite']]
    
    if not favorite_emails:
        st.info("No favorite emails yet. Add some by clicking the heart icon!")
    else:
        for idx, email in enumerate(reversed(favorite_emails)):
            with st.expander(
                f"{email['timestamp']} - {email['metadata']['recipient']} - {email['metadata']['purpose']}",
                expanded=False
            ):
                col1, col2 = st.columns([4,1])
                with col1:
                    st.write(f"**Tone:** {email['metadata']['tone']}")
                    if email['metadata'].get('preset'):
                        st.write(f"**Template:** {email['metadata']['preset']}")
                    st.code(email['content'], language="text")
                with col2:
                    if st.button("❤️ Remove", key=f"fav_remove_{idx}"):
                        original_idx = len(st.session_state.history) - 1 - next(
                            i for i, e in enumerate(reversed(st.session_state.history)) 
                            if e['timestamp'] == email['timestamp']
                        )
                        st.session_state.history[original_idx]['favorite'] = False
                        st.rerun()
                    
                    if st.button("📝 Load", key=f"fav_load_{idx}"):
                        st.session_state.generated_email = email['content']
                        st.session_state.edit_mode = False
                        st.session_state.current_tab = "📧 Email Generator"
                        st.rerun()