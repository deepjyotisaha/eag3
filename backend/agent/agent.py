import logging
from typing import List, Dict, Any
from .tools import (
    fetch_emails,
    analyze_newsletters,
    summarize_newsletters,
    format_digest
)
from .llm import plan_next_step

logger = logging.getLogger(__name__)

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
            'digest': None
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
                return state['digest'] or "# Newsletter Digest\n\nNo newsletters found in the analyzed emails."
            
            if not plan['tool'] or plan['tool'] not in TOOLS:
                logger.error(f"Invalid tool selected: {plan['tool']}")
                raise ValueError(f"Invalid tool selected: {plan['tool']}")
            
            # Execute the planned step
            tool_func = TOOLS[plan['tool']]['function']
            
            # Skip newsletter analysis if no newsletters were found
            if plan['tool'] == 'analyze_newsletters' and state['emails']:
                analyzed_emails = tool_func(state['emails'])
                newsletter_count = sum(1 for email in analyzed_emails if email.get('is_newsletter', False))
                if newsletter_count == 0:
                    logger.info("No newsletters found in the emails")
                    return "# Newsletter Digest\n\nNo newsletters found in the analyzed emails."
                state['newsletters'] = analyzed_emails
                continue
            
            if plan['tool'] == 'fetch_emails':
                state['emails'] = tool_func(email_count)
            elif plan['tool'] == 'analyze_newsletters':
                state['newsletters'] = tool_func(state['emails'])
            elif plan['tool'] == 'summarize_newsletters':
                state['summarized_newsletters'] = tool_func(state['newsletters'])
            elif plan['tool'] == 'format_digest':
                state['digest'] = tool_func(state['summarized_newsletters'])
            
            logger.info(f"Completed step: {plan['tool']}")
            
    except Exception as e:
        logger.error(f"Error in invoke_agent: {str(e)}")
        raise 