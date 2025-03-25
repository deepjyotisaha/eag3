# Gmail Newsletter Digest Extension

A Chrome extension that automatically processes your Gmail inbox to identify, summarize, and create a digest of newsletters. Built with Python backend and Chrome extension frontend.

## Features

- 🔍 Automatically identifies newsletters in your Gmail inbox
- 📝 Generates concise summaries of newsletter content
- 📋 Creates a well-formatted markdown digest
- 🔒 Secure Gmail API integration
- 🤖 Powered by Google's Gemini AI for intelligent processing
- 📊 Configurable number of emails to process
- 🔄 Real-time processing and updates

## Project Structure

```
gmail-extension/
├── backend/                 # Python backend
│   ├── agent/              # AI agent for email processing
│   │   ├── agent.py        # Main agent logic
│   │   ├── llm.py          # LLM integration
│   │   └── tools.py        # Email processing tools
│   ├── app.py              # Flask server
│   └── logging_config.py   # Logging configuration
├── extension/              # Chrome extension
│   ├── manifest.json       # Extension manifest
│   ├── popup.html         # Extension popup UI
│   ├── popup.js           # Popup logic
│   └── styles.css         # Extension styles
└── logs/                  # Application logs
```

## Prerequisites

- Python 3.8+
- Google Cloud Project with Gmail API enabled
- Chrome browser
- Google API credentials

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd gmail-extension
```

2. Set up Python environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure Google API:
   - Create a project in Google Cloud Console
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Download credentials and save as `backend/credentials.json`

4. Install Chrome Extension:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select the `extension` directory

## Usage

1. Start the backend server:
```bash
cd backend
python app.py
```

2. Click the extension icon in Chrome
3. Enter the number of emails to process
4. Click "Generate Digest"
5. View the generated newsletter digest

## Security

- All sensitive files are protected and not tracked in git:
  - `credentials.json`
  - `token.pickle`
  - `.env` files
  - Security keys and certificates
  - Log files

## Logging

Logs are stored in the `logs` directory with the following format:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## Development

- Backend: Python with Flask
- Frontend: HTML, CSS, JavaScript
- AI: Google's Gemini AI
- API: Gmail API

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Version History

- v5.0.0: Improved logging and security
- v4.0.1: Enhanced newsletter identification
- v3.0.1: Added digest formatting
- v3.0.0: Implemented AI-powered summarization
- v2.0.0: Initial release with basic functionality 