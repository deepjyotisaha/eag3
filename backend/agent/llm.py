import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any
import json

# Configure logging with detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

logger.info("Configuring Gemini API...")
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    logger.info("Gemini API configured successfully")
except Exception as e:
    logger.error(f"Error configuring Gemini API: {str(e)}")
    raise

def identify_newsletters(emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Use LLM to identify which emails are newsletters.
    """
    logger.info(f"Starting newsletter identification for {len(emails)} emails")
    
    # Create a safe version of emails for the prompt
    safe_emails = []
    for email in emails:
        safe_email = {
            'subject': email.get('subject', ''),
            'from': email.get('from', ''),
            'content': email.get('content', '')[:500]  # Limit content length
        }
        safe_emails.append(safe_email)
        logger.debug(f"Processed email: {safe_email['subject']} from {safe_email['from']}")
    
    prompt = f"""
    Analyze these emails and identify which ones are newsletters. A newsletter typically:
    - Has a regular distribution pattern
    - Contains curated content
    - Often has an unsubscribe link
    - Is from a business, organization, or service
    
    Emails to analyze:
    {json.dumps(safe_emails, indent=2)}
    
    Return a JSON array of the emails that are newsletters, with an additional field 'is_newsletter: true'.
    Format your response as a valid JSON array only, with no additional text.
    """
    
    logger.info("Making LLM call to identify newsletters")
    try:
        response = model.generate_content(prompt)
        logger.debug(f"LLM Response for newsletter identification: {response.text}")
        
        # Try to parse the response as JSON
        newsletters = json.loads(response.text)
        logger.info(f"Successfully identified {len(newsletters)} newsletters")
        for newsletter in newsletters:
            logger.debug(f"Identified newsletter: {newsletter['subject']} from {newsletter['from']}")
        return newsletters
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {str(e)}")
        logger.error(f"Raw response: {response.text}")
        return []
    except Exception as e:
        logger.error(f"Error identifying newsletters: {str(e)}")
        return []

def generate_summaries(newsletters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Use LLM to generate summaries of the newsletters.
    """
    logger.info(f"Starting summary generation for {len(newsletters)} newsletters")
    summarized_newsletters = []
    
    for i, newsletter in enumerate(newsletters, 1):
        logger.info(f"Generating summary for newsletter {i}/{len(newsletters)}: {newsletter['subject']}")
        
        prompt = f"""
        Generate a concise summary of this newsletter:
        
        Subject: {newsletter['subject']}
        From: {newsletter['from']}
        Content: {newsletter['content']}
        
        Focus on:
        1. Main topics or themes
        2. Key points or highlights
        3. Any calls to action
        
        Return the summary in a clear, structured format.
        """
        
        logger.debug(f"Making LLM call for summary generation of: {newsletter['subject']}")
        response = model.generate_content(prompt)
        logger.debug(f"LLM Response for summary: {response.text}")
        
        newsletter['summary'] = response.text
        summarized_newsletters.append(newsletter)
        logger.info(f"Completed summary for: {newsletter['subject']}")
    
    return summarized_newsletters

def create_markdown_digest(summarized_newsletters: List[Dict[str, Any]]) -> str:
    """
    Create a markdown-formatted digest of the newsletter summaries.
    """
    logger.info("Starting markdown digest creation")
    
    prompt = f"""
    Create a well-formatted markdown digest of these newsletter summaries:
    
    {summarized_newsletters}
    
    Format it as:
    # Newsletter Digest
    
    ## [Newsletter Name/Subject]
    [Summary content]
    
    Include a brief introduction and conclusion.
    """
    
    logger.debug("Making LLM call for markdown digest creation")
    response = model.generate_content(prompt)
    logger.debug(f"LLM Response for markdown digest: {response.text}")
    
    logger.info("Successfully created markdown digest")
    return response.text

def plan_next_step(current_state: Dict[str, Any], available_tools: List[str]) -> Dict[str, Any]:
    """
    Use LLM to plan the next step in the email processing pipeline.
    
    Args:
        current_state (Dict[str, Any]): Current state of the pipeline including:
            - emails: List of fetched emails
            - newsletters: List of identified newsletters
            - summarized_newsletters: List of newsletters with summaries
            - digest: Current digest if any
        available_tools (List[str]): List of available tool names
        
    Returns:
        Dict[str, Any]: Next step to take, including:
            - tool: Name of the tool to invoke
            - reason: Explanation for choosing this tool
            - is_complete: Whether the goal has been achieved
    """
    logger.info("Planning next step in the pipeline")
    
    prompt = f"""
    You are a planning agent for a Gmail newsletter digest system. Your goal is to process emails and create a newsletter digest.
    
    Current state:
    {json.dumps(current_state, indent=2)}
    
    Available tools:
    {json.dumps(available_tools, indent=2)}
    
    Analyze the current state and available tools to determine:
    1. Which tool should be invoked next
    2. Why this tool is the best choice
    3. Whether the overall goal has been achieved
    
    Return your response as a JSON object with:
    - tool: The name of the tool to invoke
    - reason: A brief explanation of why this tool is needed
    - is_complete: Boolean indicating if the goal is achieved
    
    Format your response as a valid JSON object only, with no additional text.
    """
    
    try:
        response = model.generate_content(prompt)
        logger.debug(f"LLM Response for planning: {response.text}")
        
        plan = json.loads(response.text)
        logger.info(f"Planned next step: {plan['tool']} - {plan['reason']}")
        return plan
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {str(e)}")
        logger.error(f"Raw response: {response.text}")
        return {'tool': None, 'reason': 'Error parsing LLM response', 'is_complete': False}
    except Exception as e:
        logger.error(f"Error in planning: {str(e)}")
        return {'tool': None, 'reason': str(e), 'is_complete': False} 