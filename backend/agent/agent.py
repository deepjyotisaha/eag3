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
    'fetch_emails': fetch_emails,
    'analyze_newsletters': analyze_newsletters,
    'summarize_newsletters': summarize_newsletters,
    'format_digest': format_digest
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
        
        # Main processing loop
        while True:
            # Plan next step
            plan = plan_next_step(state, list(TOOLS.keys()))
            logger.info(f"Planned next step: {plan['tool']} - {plan['reason']}")
            
            if plan['is_complete']:
                logger.info("Pipeline completed successfully")
                return state['digest'] or "# Newsletter Digest\n\nNo newsletters found in the analyzed emails."
            
            if not plan['tool'] or plan['tool'] not in TOOLS:
                logger.error(f"Invalid tool selected: {plan['tool']}")
                raise ValueError(f"Invalid tool selected: {plan['tool']}")
            
            # Execute the planned step
            tool_func = TOOLS[plan['tool']]
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