import logging
from typing import List, Dict, Any
from .tools import (
    fetch_emails,
    analyze_newsletters,
    summarize_newsletters,
    format_digest
)
from .llm import plan_next_step
from .tool_manifests import TOOL_MANIFESTS
import os

# Get logger for this module
logger = logging.getLogger(__name__)

# Log the start of a new session
logger.info("Starting new logging session")

# Define available tools and their functions
TOOLS = {
    'fetch_emails': {
        'function': fetch_emails,
        'manifest': TOOL_MANIFESTS['fetch_emails']
    },
    'analyze_newsletters': {
        'function': analyze_newsletters,
        'manifest': TOOL_MANIFESTS['analyze_newsletters']
    },
    'summarize_newsletters': {
        'function': summarize_newsletters,
        'manifest': TOOL_MANIFESTS['summarize_newsletters']
    },
    'format_digest': {
        'function': format_digest,
        'manifest': TOOL_MANIFESTS['format_digest']
    }
}

def prepare_tool_params(tool_name: str, state: Dict[str, Any], email_count: int) -> Dict[str, Any]:
    """
    Prepare tool parameters based on the tool's manifest requirements.
    
    Args:
        tool_name (str): Name of the tool to prepare parameters for
        state (Dict[str, Any]): Current state of the agent
        email_count (int): Number of emails to process
        
    Returns:
        Dict[str, Any]: Prepared parameters for the tool
    """
    tool_manifest = TOOLS[tool_name]['manifest']
    tool_params = {}
    
    for param_name, param_info in tool_manifest['input_params'].items():
        if param_name == 'num_emails':
            tool_params[param_name] = email_count
        elif param_name in state:
            value = state[param_name]
            
            # Apply filtering if specified in the manifest
            if param_info.get('filter'):
                filter_info = param_info['filter']
                if isinstance(value, list):
                    value = [
                        item for item in value 
                        if item.get(filter_info['field']) == filter_info['value']
                    ]
            
            tool_params[param_name] = value
                
    return tool_params

def update_state(state: Dict[str, Any], tool_name: str, result: Any) -> Dict[str, Any]:
    """
    Update state based on the tool's manifest requirements.
    
    Args:
        state (Dict[str, Any]): Current state
        tool_name (str): Name of the tool that was executed
        result (Any): Result from the tool execution
        
    Returns:
        Dict[str, Any]: Updated state
    """
    tool_manifest = TOOLS[tool_name]['manifest']
    state_updates = tool_manifest['state_requirements']['writes']
    
    for state_key in state_updates:
        state[state_key] = result
            
    return state

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
            name: {
                'description': tool['manifest']['description'],
                'input_params': tool['manifest']['input_params'],
                'output_params': tool['manifest']['output_params']
            }
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
            
            # Get the tool function and prepare parameters
            tool_name = plan['tool']
            tool_params = prepare_tool_params(tool_name, state, email_count)
            tool_func = TOOLS[tool_name]['function']
            
            # Execute the tool with parameters
            result = tool_func(**tool_params)
            
            # Update state based on the tool's result
            state = update_state(state, tool_name, result)
            
            logger.info(f"Completed step: {tool_name}")
            
    except Exception as e:
        logger.error(f"Error in invoke_agent: {str(e)}")
        raise 