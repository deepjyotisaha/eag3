import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any
import json
import sys
import os
import re

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Get logger for this module
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

def clean_json_response(text: str) -> str:
    """
    Clean the LLM response to ensure it's valid JSON.
    Handles markdown formatting and other common issues.
    
    Args:
        text (str): Raw response text from LLM
        
    Returns:
        str: Cleaned JSON string
    """
    # Log the raw response for debugging
    #logger.debug(f"Raw response: {text}")
    
    # Remove markdown code block markers if present
    text = text.replace('```json', '').replace('```', '')
    
    # Remove any leading/trailing whitespace and newlines
    text = text.strip()
    
    # Remove any hidden characters
    text = ''.join(char for char in text if char.isprintable() or char in '\n\r\t')
    
    # Remove any trailing commas before closing brackets/braces
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    
    # Log the cleaned response for debugging
    #logger.debug(f"Cleaned response: {text}")
    
    return text

def identify_newsletters(emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Use LLM to identify which emails are newsletters.
    
    Args:
        emails (List[Dict[str, Any]]): List of email dictionaries to analyze
        
    Returns:
        List[Dict[str, Any]]: List of emails with added is_newsletter flag
    """
    try:
        # Create a safe version of emails for the prompt
        safe_emails = []
        for email in emails:
            safe_email = {
                'subject': email.get('subject', ''),
                'from': email.get('from', ''),
                'content': email.get('content', '')[:1000]  # Limit content length
            }
            safe_emails.append(safe_email)
        
        prompt = f"""
        Analyze these emails and identify which ones are newsletters.
        A newsletter is a regularly distributed publication about a particular topic or set of topics.
        
        Emails to analyze:
        {json.dumps(safe_emails, indent=2)}
        
        For each email, determine if it's a newsletter based on the following characteristics:
        1. Regular distribution pattern
        2. Topic-focused content
        3. Mass distribution characteristics
        4. Newsletter-like formatting
        5. The email is from a newsletter service provider which is either an individual or an organization
        6. Emails promoting products or services are not newsletters, job alerts are not newsletters
        
        Return a JSON array where each object has:
        {{
            "subject": "email subject",
            "from": "sender email",
            "is_newsletter": true/false
        }}
        
        IMPORTANT:
        1. Return ONLY the JSON array, no other text
        2. Include ALL emails from the input, not just newsletters
        3. Set is_newsletter to false for non-newsletter emails
        4. Match the subject and from fields exactly with the input emails
        5. Respond with raw JSON only, no markdown or code blocks
        6. DO NOT wrap the response in ```json or any other markdown formatting
        7. Start your response with a single [ character and end with a single ] character
        """
        
        logger.info("Sending prompt to LLM for newsletter identification")
        response = model.generate_content(prompt)
        #logger.debug(f"Response attributes: {dir(response)}")
        
        if not hasattr(response, 'text'):
            logger.error("Response object does not have 'text' attribute")
            logger.error(f"Available attributes: {dir(response)}")
            return []
            
        logger.debug(f"LLM Response for newsletter identification: {response.text}")
        
        # Clean and parse the response as JSON
        cleaned_response = clean_json_response(response.text)
        newsletters = json.loads(cleaned_response)
        
        # Validate and filter newsletters to match input emails
        valid_newsletters = []
        for email in emails:
            matching_newsletter = next(
                (n for n in newsletters 
                 if n['subject'] == email['subject'] and n['from'] == email['from']),
                None
            )
            if matching_newsletter:
                # Add is_newsletter flag to original email
                email['is_newsletter'] = matching_newsletter['is_newsletter']
                valid_newsletters.append(email)
            else:
                # If no match found, mark as not a newsletter
                email['is_newsletter'] = False
                valid_newsletters.append(email)
        
        newsletter_count = sum(1 for email in valid_newsletters if email['is_newsletter'])
        logger.info(f"Successfully identified {newsletter_count} newsletters out of {len(emails)} emails")
        
        return valid_newsletters
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {str(e)}")
        logger.error(f"Raw response: {response.text}")
        return []
    except Exception as e:
        logger.error(f"Error identifying newsletters: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
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

        Keep the summary concise and to the point and do not exceed 200 words.
        
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

def plan_next_step(current_state: Dict[str, Any], available_tools: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use LLM to plan the next step in the email processing pipeline.
    
    Args:
        current_state (Dict[str, Any]): Current state of the pipeline including:
            - emails: List of fetched emails
            - newsletters: List of identified newsletters
            - summarized_newsletters: List of newsletters with summaries
            - digest: Current digest if any
        available_tools (Dict[str, Any]): Dictionary of available tools with their descriptions,
            input parameters, output parameters, and state requirements
        
    Returns:
        Dict[str, Any]: Next step to take, including:
            - tool: Name of the tool to invoke
            - reason: Explanation for choosing this tool
            - is_complete: Whether the goal has been achieved
    """
    logger.info("Planning next step in the pipeline")
    
    # Create a more detailed prompt that includes tool requirements
    prompt = f"""
    You are a planning agent for a Gmail newsletter digest generator. Your goal is to process emails and create a single digest with summaries of identified newsletters.
    
    Current state:
    {json.dumps(current_state, indent=2)}
    
    Available tools:
    {json.dumps(available_tools, indent=2)}
    
    For each tool, consider:
    1. Input parameters required and their types
    2. Output parameters and their structure
    3. State requirements (what state it reads and writes)

    Return a JSON object with:
    {{
        "tool": "name of the tool to use",
        "reason": "explanation of why this tool was chosen",
        "is_complete": true or false # Set to true only after format_digest has been executed and state contains digest, else set to false
    }}
    
    Rules for planning:
    1. Only choose a tool if its required input parameters are available in the current state
    2. Consider the state dependencies (what state each tool reads and writes)
    3. The pipeline is complete ONLY when all the following conditions are met:
       - We have fetched emails
       - We have identified newsletters
       - We have generated summaries for newsletters
       - We have formatted the final digest
    4. Tools must be used in a logical order based on their dependencies
    5. NEVER mark the task as complete until the format_digest tool has been called and the digest is in the state
    
    ALWAYS REMEMBER:
    1. Return ONLY the JSON object, no other text
    2. Respond with raw JSON only, no markdown or code blocks
    3. DO NOT wrap the response in ```json or any other markdown formatting
    4. Set is_complete to true ONLY after format_digest has been called and the digest is in the state
    """
    
    logger.debug("Making LLM call for next step planning")
    response = model.generate_content(prompt)
    logger.debug(f"LLM Response for planning: {response.text}")
    
    try:
        # Clean and parse the response
        cleaned_response = clean_json_response(response.text)
        plan = json.loads(cleaned_response)
        
        # Validate the plan
        if not isinstance(plan, dict) or 'tool' not in plan or 'reason' not in plan or 'is_complete' not in plan:
            logger.error("Invalid plan format")
            return {'tool': None, 'reason': 'Invalid plan format', 'is_complete': False}
            
        # Validate tool selection
        if plan['tool'] and plan['tool'] not in available_tools:
            logger.error(f"Invalid tool selected: {plan['tool']}")
            return {'tool': None, 'reason': f'Invalid tool selected: {plan["tool"]}', 'is_complete': False}
            
        return plan
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {str(e)}")
        logger.error(f"Raw response: {response.text}")
        return {'tool': None, 'reason': 'Error parsing response', 'is_complete': False}
    except Exception as e:
        logger.error(f"Error in plan_next_step: {str(e)}")
        return {'tool': None, 'reason': f'Error: {str(e)}', 'is_complete': False} 