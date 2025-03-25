import logging
from typing import List, Dict, Any
from .tools import (
    fetch_emails,
    analyze_newsletters,
    summarize_newsletters,
    format_digest
)
from .llm import plan_next_step
import os

# Get logger for this module
logger = logging.getLogger(__name__)

# Log the start of a new session
logger.info("Starting new logging session")

# Define available tools and their functions
TOOLS = {
    'fetch_emails': {
        'function': fetch_emails,
        'description': 'This tool fetches emails from Gmail, takes a number of emails to fetch as input, and returns a list of email dictionaries containing subject, sender, and content'
    },
    'analyze_newsletters': {
        'function': analyze_newsletters,
        'description': 'This tool analyzes emails, takes a list of email dictionaries, analyzes them and returns the identified newsletters with an added flag is_newsletter'
    },
    'summarize_newsletters': {
        'function': summarize_newsletters,
        'description': 'This tool generates summaries of newsletters, takes a list of identified newsletters, and returns the same list with added summary field for each newsletter'
    },
    'format_digest': {
        'function': format_digest,
        'description': 'This tool formats newsletter summaries into a markdown digest, takes a list of summarized newsletters, and returns a markdown-formatted string with introduction, sections, and conclusion'
    }
}

def invoke_agent(email_count: int) -> str:
    """
    Main agent function that orchestrates the email processing pipeline using LLM for planning.
    
    Args:
        email_count (int): Number of emails to process
        
    Returns:
        str: Markdown formatted digest of newsletters
    """
    logger.info(f"Starting email processing pipeline for {email_count} emails")
    
    try:
        # Initialize state
        state = {
            'emails': [],
            'newsletters': [],
            'summarized_newsletters': [],
            'digest': None,
            'email_count': email_count
        }
        
        # Create a serializable version of tools for the LLM
        tools_for_llm = {
            name: {'description': tool['description']}
            for name, tool in TOOLS.items()
        }
        
        # Main processing loop
        while True:
            # Plan next step
            plan = plan_next_step(state, tools_for_llm)
            logger.info(f"Planned next step: {plan['tool']} - {plan['reason']}")
            
            if plan['is_complete']:
                logger.info("Pipeline completed successfully")
                logger.info(f"Final state: emails={len(state['emails'])}, newsletters={len(state['newsletters'])}, summarized={len(state['summarized_newsletters'])}, digest={bool(state['digest'])}")
                if state['digest']:
                    logger.info("Digest content: %s", state['digest'][:100] + "..." if len(state['digest']) > 100 else state['digest'])
                return state['digest'] or "# Newsletter Digest\n\nNo newsletters found in the analyzed emails."
            
            if not plan['tool'] or plan['tool'] not in TOOLS:
                logger.error(f"Invalid tool selected: {plan['tool']}")
                raise ValueError(f"Invalid tool selected: {plan['tool']}")
            
            # Get the tool function
            tool_name = plan['tool']
            tool_params = plan.get('parameters', {})
            
            # Get the tool function
            tool_func = TOOLS[tool_name]['function']
            
            # Prepare parameters based on tool requirements
            if tool_name == 'fetch_emails':
                tool_params['num_emails'] = email_count
            elif tool_name == 'analyze_newsletters':
                tool_params['emails'] = state['emails']
            elif tool_name == 'summarize_newsletters':
                # Only pass newsletters where is_newsletter is true
                newsletters = [email for email in state['newsletters'] if email.get('is_newsletter', False)]
                tool_params['newsletters'] = newsletters
            elif tool_name == 'format_digest':
                # Only pass summarized newsletters where is_newsletter is true
                summarized = [email for email in state['summarized_newsletters'] if email.get('is_newsletter', False)]
                tool_params['summarized_newsletters'] = summarized
            
            # Execute the tool with parameters
            result = tool_func(**tool_params)
            
            # Update state based on the tool's result
            if tool_name == 'fetch_emails':
                state['emails'] = result
            elif tool_name == 'analyze_newsletters':
                state['newsletters'] = result
            elif tool_name == 'summarize_newsletters':
                # Only store summarized newsletters where is_newsletter is true
                state['summarized_newsletters'] = [email for email in result if email.get('is_newsletter', False)]
            elif tool_name == 'format_digest':
                state['digest'] = result
                logger.info(f"Updated digest: {bool(result)}")
                if result:
                    logger.info("Digest content: %s", result[:100] + "..." if len(result) > 100 else result)
            
            logger.info(f"Completed step: {tool_name}")
            
    except Exception as e:
        logger.error(f"Error in invoke_agent: {str(e)}")
        raise 