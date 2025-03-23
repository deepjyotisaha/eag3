import logging
from typing import List, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os
import base64
from email.mime.text import MIMEText
from .llm import identify_newsletters, generate_summaries, create_markdown_digest

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            credentials_path = os.path.join(current_dir, '..', 'credentials.json')
            
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"credentials.json not found at {credentials_path}")
                
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def get_email_content(service, msg_id):
    try:
        message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        headers = message['payload']['headers']
        subject = next(header['value'] for header in headers if header['name'].lower() == 'subject')
        from_header = next(header['value'] for header in headers if header['name'].lower() == 'from')
        
        # Get email body
        if 'parts' in message['payload']:
            parts = message['payload']['parts']
            data = parts[0]['body'].get('data', '')
        else:
            data = message['payload']['body'].get('data', '')
            
        if data:
            text = base64.urlsafe_b64decode(data).decode()
        else:
            text = "No content"
            
        return {
            'subject': subject,
            'from': from_header,
            'content': text
        }
    except Exception as e:
        logger.error(f"Error getting email content for message {msg_id}: {str(e)}")
        return {'error': str(e)}

def fetch_emails(num_emails=10) -> List[Dict[str, Any]]:
    """
    Tool to fetch emails from Gmail.
    
    Args:
        num_emails (int): Number of emails to fetch (default: 10)
        
    Returns:
        list: List of email dictionaries containing subject, sender, and content
    """
    try:
        logger.info(f"Fetching {num_emails} emails from Gmail")
        service = get_gmail_service()
        
        # Get list of emails
        results = service.users().messages().list(userId='me', maxResults=num_emails).execute()
        messages = results.get('messages', [])
        
        if not messages:
            logger.info("No messages found")
            return []
        
        emails = []
        for message in messages:
            email_data = get_email_content(service, message['id'])
            if 'error' not in email_data:
                emails.append(email_data)
            
        logger.info(f"Successfully retrieved {len(emails)} emails")
        return emails
        
    except Exception as e:
        logger.error(f"Error in fetch_emails: {str(e)}")
        raise

def analyze_newsletters(emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Tool to analyze emails and identify which ones are newsletters.
    
    Args:
        emails (List[Dict[str, Any]]): List of email dictionaries containing subject, sender, and content
        
    Returns:
        List[Dict[str, Any]]: List of identified newsletters with additional 'is_newsletter' field
    """
    logger.info(f"Starting newsletter analysis for {len(emails)} emails")
    return identify_newsletters(emails)

def summarize_newsletters(newsletters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Tool to generate concise summaries of newsletters.
    
    Args:
        newsletters (List[Dict[str, Any]]): List of newsletter dictionaries
        
    Returns:
        List[Dict[str, Any]]: List of newsletters with added 'summary' field containing structured summaries
    """
    logger.info(f"Starting newsletter summarization for {len(newsletters)} newsletters")
    return generate_summaries(newsletters)

def format_digest(summarized_newsletters: List[Dict[str, Any]]) -> str:
    """
    Tool to format newsletter summaries into a markdown digest.
    
    Args:
        summarized_newsletters (List[Dict[str, Any]]): List of newsletters with summaries
        
    Returns:
        str: Markdown-formatted digest with introduction, newsletter sections, and conclusion
    """
    logger.info("Starting digest formatting")
    return create_markdown_digest(summarized_newsletters) 