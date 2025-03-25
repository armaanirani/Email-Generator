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
if 'selected_preset' not in st.session_state:
    st.session_state.selected_preset = None

# Define email presets
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

# File processing functions (keep your existing functions here)
# ... [keep all your existing file processing functions] ...

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

    # Preset selection
    with st.expander("📁 Email Presets", expanded=False):
        preset_col1, preset_col2 = st.columns([3, 1])
        with preset_col1:
            selected_preset_name = st.selectbox(
                "Choose a template:",
                ["Custom Email"] + list(EMAIL_PRESETS.keys()),
                index=0
            )
        with preset_col2:
            if selected_preset_name != "Custom Email":
                if st.button("Load Preset"):
                    st.session_state.selected_preset = EMAIL_PRESETS[selected_preset_name]
                    st.rerun()
        
        if st.session_state.selected_preset:
            st.info(f"Loaded preset: {selected_preset_name}")
            if st.button("Clear Preset"):
                st.session_state.selected_preset = None
                st.rerun()

    # Email configuration options
    with st.expander("⚙️ Email Configuration", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            tone = st.selectbox(
                "Select Tone:",
                ["Professional", "Friendly", "Casual", "Persuasive", "Sympathetic"],
                index=["Professional", "Friendly", "Casual", "Persuasive", "Sympathetic"].index(
                    st.session_state.selected_preset["tone"] if st.session_state.selected_preset else "Professional"
                )
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

        email_purpose = st.text_area(
            "Purpose of the Email:",
            value=st.session_state.selected_preset["purpose"] if st.session_state.selected_preset else ""
        )
        
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

    # If preset is loaded and this is first render, populate the fields
    if st.session_state.selected_preset and 'preset_loaded' not in st.session_state:
        st.session_state.generated_email = st.session_state.selected_preset["template"]
        st.session_state.preset_loaded = True
        st.session_state.edit_mode = False

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
                            "purpose": email_purpose[:50],
                            "preset": selected_preset_name if selected_preset_name != "Custom Email" else None
                        }
                    }
                    st.session_state.history.append(email_record)
                    # Keep only last 10 history items
                    if len(st.session_state.history) > 10:
                        st.session_state.history = st.session_state.history[-10:]
                    st.session_state.generated_email = generated_email
                    st.session_state.edit_mode = False
                    st.session_state.selected_preset = None  # Clear preset after generation
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
                    if email['metadata'].get('preset'):
                        st.write(f"**Template:** {email['metadata']['preset']}")
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
                    if email['metadata'].get('preset'):
                        st.write(f"**Template:** {email['metadata']['preset']}")
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