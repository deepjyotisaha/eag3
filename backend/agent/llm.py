import google.generativeai as genai
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import json
import sys
import os
import re

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import logger factory and get logger
from backend.logger_factory import LoggerFactory
logger = LoggerFactory.get_logger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    logger.error("GOOGLE_API_KEY not found in environment variables")
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

logger.debug("Configuring Gemini API...")  # Changed to debug
try:
    # Configure the API
    genai.configure(api_key=api_key)
    logger.debug("Gemini API configured successfully")  # Changed to debug
    
    # List available models
    available_models = genai.list_models()
    model_names = [model.name for model in available_models]
    logger.debug(f"Available models: {model_names}")  # Changed to debug
    
    # Check if our desired model is available
    desired_model = 'gemini-2.0-flash'
    full_model_name = f'models/{desired_model}'
    if full_model_name not in model_names:
        logger.error(f"Model {full_model_name} not found in available models")
        logger.error("Please check the API documentation for the correct model name")
        raise ValueError(f"Model {full_model_name} not available")
    
    # Try to get the model
    model = genai.GenerativeModel(desired_model)  # Use base name without prefix
    # Test the model with a simple prompt
    test_response = model.generate_content("Generate a poem about spring flowers")
    logger.debug(f"Test response: {test_response.text}")  # Changed to debug
    logger.debug("Model test successful")  # Changed to debug
    
except Exception as e:
    logger.error(f"Error configuring Gemini API: {str(e)}")
    logger.error(f"Error type: {type(e).__name__}")
    logger.error(f"Error details: {str(e)}")
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
    logger.debug(f"Raw response: {text}")
    
    # Remove markdown code block markers if present
    text = text.replace('```json', '').replace('```', '')
    
    # Remove any leading/trailing whitespace and newlines
    text = text.strip()
    
    # Remove any hidden characters
    text = ''.join(char for char in text if char.isprintable() or char in '\n\r\t')
    
    # Remove any trailing commas before closing brackets/braces
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    
    # Log the cleaned response for debugging
    logger.debug(f"Cleaned response: {text}")
    
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
        
        For each email, determine if it's a newsletter based on:
        1. Regular distribution pattern
        2. Topic-focused content
        3. Mass distribution characteristics
        4. Newsletter-like formatting
        
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
        logger.debug(f"Response attributes: {dir(response)}")
        
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
        available_tools (Dict[str, Any]): Dictionary of available tools with their descriptions
        
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
    
    Available tools and their descriptions:
    {json.dumps(available_tools, indent=2)}
    
    Analyze the current state and available tools to determine:
    1. Which tool should be invoked next
    2. Why this tool is the best choice
    3. Whether the overall goal has been achieved
    
    Example response for any state:
    {{
        "tool": "tool_name",
        "reason": "Clear explanation based on current state",
        "is_complete": false
    }}
    
    You MUST return a valid JSON object with exactly these fields:
    {{
        "tool": "name_of_tool_to_invoke",
        "reason": "explanation_of_choice",
        "is_complete": true_or_false
    }}
    
    IMPORTANT: 
    1. Return ONLY the JSON object, no other text
    2. The tool field must be one of the available tools listed above
    3. The is_complete field must be a boolean (true or false)
    4. The reason field must be a string explaining your choice
    5. Respond with raw JSON only, no markdown or code blocks
    6. DO NOT wrap the response in ```json or any other markdown formatting
    7. Start your response with a single {{ character and end with a single }} character
    """
    
    #logger.info("Planning prompt:")
    #logger.info(prompt)
    #logger.info("End of planning prompt")

    try:
        response = model.generate_content(prompt)
        logger.info("Planning response:")
        logger.info(response.text)
        logger.info("End of planning response")
        
        logger.debug(f"LLM Response for planning: {response.text}")
        
        # Add detailed logging for JSON parsing
        logger.info("Attempting to parse response as JSON...")
        logger.info(f"Response type: {type(response.text)}")
        logger.info(f"Response length: {len(response.text)}")
        logger.info(f"Raw response text: {repr(response.text)}")  # repr() will show any hidden characters
        
        # Check for empty response
        if not response.text or response.text.strip() == '':
            logger.error("Received empty response from LLM")
            return {'tool': 'fetch_emails', 'reason': 'Starting with email fetch as no response received', 'is_complete': False}
            
        # Clean and parse the response as JSON
        cleaned_response = clean_json_response(response.text)
        plan = json.loads(cleaned_response)
        
        # Validate required fields
        required_fields = {'tool', 'reason', 'is_complete'}
        if not all(field in plan for field in required_fields):
            logger.error(f"Missing required fields in response. Got: {list(plan.keys())}")
            return {'tool': 'fetch_emails', 'reason': 'Starting with email fetch due to invalid response format', 'is_complete': False}
            
        logger.info(f"Planned next step: {plan['tool']} - {plan['reason']}")
        return plan
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {str(e)}")
        logger.error(f"Raw response: {response.text}")
        logger.error(f"Error position: {e.pos}")
        logger.error(f"Error line: {e.lineno}")
        logger.error(f"Error column: {e.colno}")
        logger.error(f"Error message: {e.msg}")
        return {'tool': 'fetch_emails', 'reason': 'Starting with email fetch due to JSON parsing error', 'is_complete': False}
    except Exception as e:
        logger.error(f"Error in planning: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        return {'tool': 'fetch_emails', 'reason': f'Starting with email fetch due to error: {str(e)}', 'is_complete': False} 