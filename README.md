# AI Email Generator ✉️

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?logo=openai&logoColor=white)](https://openai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Demo](#demo)
- [Installation](#installation)
- [Dependencies](#dependencies)
- [Usage](#usage)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Contact](#contact)

## Overview

### Description
The AI Email Generator is a professional email composition assistant built with Streamlit that leverages OpenAI's powerful language models to help users craft perfectly structured emails. With customizable templates, tone control, and attachment analysis, this app generates polished emails for various professional scenarios including job applications, follow-ups, sales pitches, and networking requests. The intuitive interface allows for easy editing, exporting, and history tracking of generated emails.

### Technology Stack
- **Frontend**: Streamlit
- **AI Engine**: OpenAI GPT models
- **Backend**: Python 3.8+
- Key Libraries:
  - `openai`
  - `python-dotenv`
  - `reportlab` (PDF generation)
  - `PyPDF2` (PDF processing)
  - `python-docx` (Word document processing)
  - `pandas` (Excel processing)

## Features

### ✨ Smart Email Generation
- Multiple professionally-designed email templates
- Customizable tone (Professional, Friendly, Casual, Persuasive, Sympathetic)
- Adjustable length (Short, Medium, Detailed)
- Support for multiple languages

### 📎 Attachment Processing
- Extract and reference content from:
  - PDF documents
  - Word files (.docx)
  - Excel spreadsheets
  - Text files
  - Images (metadata only)
- Automatic content analysis for email relevance

### 📂 Email Management
- History tracking of generated emails
- Favorite/star important emails
- Search and filter by recipient, date, or purpose
- One-click reload of previous emails

### 💾 Export Options
- Save as PDF with professional formatting
- Export as plain text files
- Copy to clipboard functionality
- Automatic filename generation

### 🖥 User-Friendly Interface
- Intuitive form-based input
- Real-time character counters
- Responsive design for all devices
- Clear error messages and validations

## Demo

### Screenshots
1. **Main Interface**  
![Email Generator Interface](https://github.com/user-attachments/assets/email-generator-1.png)

2. **Presets Selection**  
![Presets Selection](https://github.com/user-attachments/assets/email-generator-2.png)

3. **Email Configuration**
![Email Configuration](https://github.com/user-attachments/assets/email-generator-2.png)

5. **Generated Email Example**  
![Generated Email](https://github.com/user-attachments/assets/email-generator-3.png)

6. **History & Favorites**  
![History Panel](https://github.com/user-attachments/assets/email-generator-4.png)


## Installation

### Prerequisites
- Python 3.8+
- OpenAI API key

### Setup
1. Clone the repository:
```bash
git clone https://github.com/armaanirani/Email-Generator.git
cd Email-Generator
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate # Linux/MacOS
venv\Scripts\activate # Windows 
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your OpenAI API key:
```env
OPENAI_API_KEY=your-api-key-here
```
## Dependencies

The app relies on the following Python libraries:

Library | Purpose | Installation Command
--------|---------|---------------------
`streamlit` | Web app framework | `pip install streamlit`
`openai` | OpenAI API integration | `pip install openai`
`python-dotenv` | Environment variables | `pip install python-dotenv`
`PyPDF2` | PDF text extraction | `pip install PyPDF2`
`python-docx` | Word document processing | `pip install python-docx`
`pandas` | Excel file processing | `pip install pandas`
`reportlib` | PDF generation | `pip install reportlib`

## Usage

1. Run the application:
```bash
streamlit run app.py
```

2. The app will open in your default browser at `http://localhost:8501`

### Main Interface

- **Email Generator Tab**:
  - Select from preset templates or create custom emails.
  - Configure email parameters (tone, length, style, language).
  - Enter sender/recipient details and email purpose.
  - Attach files for context (content will be extracted).
  - Generate, edit, and export emails.

- **History & Favorites Tab**:
  - View previously generated emails.
  - Mark emails as favorites.
  - Load previous emails for reuse.
  - Delete history items.

### File Support

The application can process these file types:
- **PDF**: Text content extracted
- **DOCX**: Text content extracted
- **XLSX**: Converted to text representation
- **TXT**: Read directly
- **Images**: Not processed (placeholder text included)

## Configuration

### Environment Variables

Set in the `.env` file:

Variable | Required | Purpose
---------|----------|--------
`OPENAI_API_KEY` | Yes | OpenAI API access

### Model Selection and Configuration

The app can be customized by modifying these constants in `app.py`:

```python
# Default model and options
DEFAULT_MODEL = "gpt-4o-mini"
MODEL_OPTIONS = ["gpt-4o", "gpt-4o-mini", "o1-mini", "o3-mini"]

# Limits
MAX_HISTORY_ITEMS = 20
MAX_FILE_SIZE_MB = 5
MAX_CONTENT_LENGTH = 3000
MAX_RETRIES = 3
```

### Custom Templates

1. Edit the `EMAIL_PRESETS` dictionary in `app.py`
2. Add new templates with:
    -`tone`: Professional/Friendly/etc.
    -`purpose`: Brief description.
    -`template`: Email template with placeholders.

### PDF Generation

Modify the `generate_pdf()` function to:
- Change the page layout.
- Adjust fonts/styles.
- Add headers/footers.

## Troubleshooting

**OpenAI API Key Not Found**:
- Ensure `.env` file exists in project root and `OPENAI_API_KEY` is set.
- Verify the key is correctly formatted and valid.

**File Processing Errors**:
- Check file size (max 5MB).
- Verify file type is supported.
- Ensure files aren't password protected.

**PDF Generation Issues**:
- Try smaller email content.
- Check for special characters that might interfere.

## Contributing

I welcome contributions to improve the Email Generator! **Before making any changes, please follow these steps:**

1. **Contact Maintainers**  
   Email [armaanirani@gmail.com](mailto:armaanirani@gmail.com) with:
   - Subject line: "Contribution Proposal: [Brief Description]"
   - Details about your proposed feature/bug fix
   - Your GitHub username

2. **Await Approval**  
   I’ll review your proposal within 3-5 business days and provide feedback/approval.

3. **Follow Development Guidelines**  
   Once approved:
   - Fork the repository
   - Create a feature branch:  
     ```bash 
     git checkout -b feature/your-feature-name
     ```
   - Implement changes with clear commit messages:
     ```bash
     git commit -m 'Added an amazing feature'
   - Test thoroughly
   - Push to your fork:  
     ```bash
     git push origin feature/your-feature-name
     ```
   - Open a Pull Request with a detailed description

### Code Standards
- Follow PEP8 conventions
- Include docstrings for all functions
- Use descriptive variable names
- Add comments for complex logic
- Ensure backward compatibility

---

## Contact

**Before contributing, please contact:**  
**Maintainer**: [Armaan Irani]  
**Email**: [armaanirani@gmail.com](mailto:armaanirani@gmail.com)  
**GitHub**: [@armaanirani](https://github.com/armaanirani)  

**Project Repository**:  
[https://github.com/armaanirani/Email-Generator](https://github.com/armaanirani/Email-Generator)  

**For Issues/Feedback**:  
- Open a ticket in [GitHub Issues](https://github.com/armaanirani/Email-Generator/issues)  
- Email with subject line "[Email Generator] - [Brief Topic]"  

**Note**: All contribution proposals must be emailed first for discussion. Unsolicited pull requests will not be accepted without prior coordination.  

---
