from typing import List, Dict, Any

TOOL_MANIFESTS = {
    'fetch_emails': {
        'name': 'fetch_emails',
        'description': 'Fetches emails from Gmail using the Gmail API',
        'input_params': {
            'num_emails': {
                'type': 'int',
                'description': 'Number of emails to fetch',
                'default': 10,
                'required': False
            }
        },
        'output_params': {
            'type': 'List[Dict[str, Any]]',
            'description': 'List of email dictionaries containing subject, sender, and content',
            'structure': {
                'subject': 'str',
                'from': 'str',
                'content': 'str'
            }
        },
        'state_requirements': {
            'reads': [],  # No state needed
            'writes': ['emails']  # Updates the emails list in state
        }
    },
    'analyze_newsletters': {
        'name': 'analyze_newsletters',
        'description': 'Analyzes emails to identify which ones are newsletters',
        'input_params': {
            'emails': {
                'type': 'List[Dict[str, Any]]',
                'description': 'List of email dictionaries to analyze',
                'required': True,
                'filter': None  # No filtering needed
            }
        },
        'output_params': {
            'type': 'List[Dict[str, Any]]',
            'description': 'List of emails with added is_newsletter flag',
            'structure': {
                'subject': 'str',
                'from': 'str',
                'content': 'str',
                'is_newsletter': 'bool'
            }
        },
        'state_requirements': {
            'reads': ['emails'],
            'writes': ['newsletters']
        }
    },
    'summarize_newsletters': {
        'name': 'summarize_newsletters',
        'description': 'Generates concise summaries of identified newsletters',
        'input_params': {
            'newsletters': {
                'type': 'List[Dict[str, Any]]',
                'description': 'List of newsletter dictionaries to summarize',
                'required': True,
                'filter': {
                    'field': 'is_newsletter',
                    'value': True
                }
            }
        },
        'output_params': {
            'type': 'List[Dict[str, Any]]',
            'description': 'List of newsletters with added summary field',
            'structure': {
                'subject': 'str',
                'from': 'str',
                'content': 'str',
                'is_newsletter': 'bool',
                'summary': 'str'
            }
        },
        'state_requirements': {
            'reads': ['newsletters'],
            'writes': ['summarized_newsletters']
        }
    },
    'format_digest': {
        'name': 'format_digest',
        'description': 'Formats newsletter summaries into a markdown digest',
        'input_params': {
            'summarized_newsletters': {
                'type': 'List[Dict[str, Any]]',
                'description': 'List of newsletters with summaries to format',
                'required': True,
                'filter': {
                    'field': 'is_newsletter',
                    'value': True
                }
            }
        },
        'output_params': {
            'type': 'str',
            'description': 'Markdown-formatted digest with introduction, sections, and conclusion'
        },
        'state_requirements': {
            'reads': ['summarized_newsletters'],
            'writes': ['digest']
        }
    }
} 