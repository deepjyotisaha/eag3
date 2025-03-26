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
python app.py --log-level DEBUG | Tee-Object -FilePath logs/agent.log
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

// ... existing content ...

## How It Works

### Agent Architecture Deep Dive

The system uses an intelligent agent architecture to process emails through a series of tools, with the LLM making decisions about tool selection and parameter preparation.

#### State Management and Decision Flow

1. **State Structure**
```python
state = {
    'emails': [],          # Raw emails from Gmail
    'newsletters': [],     # Emails with newsletter identification
    'summarized_newsletters': [], # Newsletters with summaries
    'digest': None,        # Final markdown digest
    'email_count': 5       # Number of emails to process
}
```

2. **LLM Decision Making**
```python
def plan_next_step(current_state: Dict[str, Any], available_tools: Dict[str, Any]) -> Dict[str, Any]:
    """
    LLM analyzes current state and available tools to decide next action.
    Example prompt structure:
    """
    prompt = f"""
    Current state:
    {json.dumps(current_state, indent=2)}
    
    Available tools:
    {json.dumps(available_tools, indent=2)}
    
    Rules for planning:
    1. Only choose tool if required inputs are in current state
    2. Consider state dependencies
    3. Pipeline complete only after format_digest
    """
    # Returns:
    return {
        "tool": "selected_tool_name",
        "reason": "explanation of choice",
        "is_complete": False
    }
```

#### Parameter Preparation Flow

1. **Tool Manifest Example**
```python
TOOLS = {
    'analyze_newsletters': {
        'manifest': {
            'input_params': {
                'emails': {
                    'type': 'List[Dict]',
                    'filter': None
                }
            },
            'state_requirements': {
                'reads': ['emails'],
                'writes': ['newsletters']
            }
        }
    }
}
```

2. **Parameter Preparation**
```python
def prepare_tool_params(tool_name: str, state: Dict[str, Any], email_count: int):
    """
    Example parameter preparation for analyze_newsletters:
    """
    # For analyze_newsletters tool
    if tool_name == 'analyze_newsletters':
        return {
            'emails': state['emails']  # Direct state transfer
        }
    
    # For summarize_newsletters tool
    if tool_name == 'summarize_newsletters':
        return {
            'newsletters': [
                n for n in state['newsletters']
                if n.get('is_newsletter') == True
            ]  # Filtered based on manifest
        }
```

### Processing Pipeline Example

1. **Initial State**
```python
state = {
    'emails': [],
    'newsletters': [],
    'summarized_newsletters': [],
    'digest': None,
    'email_count': 5
}
```

2. **After Fetch Emails**
```python
state = {
    'emails': [
        {
            'subject': 'Tech Newsletter #123',
            'from': 'tech@news.com',
            'content': '...'
        },
        # ... more emails
    ],
    'newsletters': [],
    'summarized_newsletters': [],
    'digest': None
}
```

3. **After Newsletter Analysis**
```python
state = {
    'emails': [...],  # Original emails preserved
    'newsletters': [
        {
            'subject': 'Tech Newsletter #123',
            'from': 'tech@news.com',
            'content': '...',
            'is_newsletter': True
        }
    ],
    'summarized_newsletters': [],
    'digest': None
}
```

### LLM Decision Examples

1. **Initial Decision**
```json
{
    "tool": "fetch_emails",
    "reason": "No emails in current state. Need to fetch emails first.",
    "is_complete": false
}
```

2. **Mid-Pipeline Decision**
```json
{
    "tool": "summarize_newsletters",
    "reason": "Newsletters identified but not summarized. Need summaries before creating digest.",
    "is_complete": false
}
```

3. **Final Decision**
```json
{
    "tool": "format_digest",
    "reason": "All newsletters summarized. Ready to create final digest.",
    "is_complete": false
}
```

### State Updates and Validation

```python
def update_state(state: Dict[str, Any], tool_name: str, result: Any):
    """
    Example state update process:
    """
    # After analyze_newsletters
    if tool_name == 'analyze_newsletters':
        state['newsletters'] = result
        # Validate newsletter format
        for newsletter in state['newsletters']:
            assert 'is_newsletter' in newsletter
    
    # After summarize_newsletters
    if tool_name == 'summarize_newsletters':
        state['summarized_newsletters'] = result
        # Validate summary format
        for newsletter in state['summarized_newsletters']:
            assert 'summary' in newsletter
    
    return state
```

### Key Implementation Features

1. **State Tracking**
   - Immutable original data
   - Progressive state updates
   - Validation at each step
   - Clear state dependencies

2. **LLM Decision Making**
   - State-based tool selection
   - Dependency awareness
   - Clear completion criteria
   - Explainable decisions

3. **Parameter Management**
   - Manifest-driven preparation
   - Automatic filtering
   - Type validation
   - Special case handling

4. **Pipeline Control**
   - Step-by-step progression
   - State consistency checks
   - Error recovery
   - Clear completion conditions

This architecture ensures reliable email processing while maintaining data integrity and providing clear decision-making throughout the pipeline.
