import logging
import os
from dotenv import load_dotenv
from agent.tools import fetch_emails, analyze_newsletters, summarize_newsletters, format_digest

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_gmail_connection():
    """Test Gmail API connection and email fetching"""
    try:
        logger.info("Testing Gmail connection...")
        emails = fetch_emails(num_emails=2)  # Fetch just 2 emails for testing
        if emails:
            logger.info(f"Successfully fetched {len(emails)} emails")
            logger.info(f"Sample email subject: {emails[0]['subject']}")
            return True
        else:
            logger.warning("No emails found")
            return False
    except Exception as e:
        logger.error(f"Error testing Gmail connection: {str(e)}")
        return False

def test_llm_components():
    """Test LLM-based components"""
    try:
        # First fetch some emails
        logger.info("Testing LLM components...")
        emails = fetch_emails(num_emails=2)
        if not emails:
            logger.error("No emails to test with")
            return False

        # Test newsletter identification
        logger.info("Testing newsletter identification...")
        newsletters = analyze_newsletters(emails)
        logger.info(f"Identified {len(newsletters)} newsletters")

        if newsletters:
            # Test summarization
            logger.info("Testing newsletter summarization...")
            summarized = summarize_newsletters(newsletters)
            logger.info(f"Generated summaries for {len(summarized)} newsletters")

            # Test digest formatting
            logger.info("Testing digest formatting...")
            digest = format_digest(summarized)
            logger.info("Successfully generated digest")
            return True
        return False
    except Exception as e:
        logger.error(f"Error testing LLM components: {str(e)}")
        return False

def main():
    """Run all tests"""
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    required_vars = ['GOOGLE_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False

    # Run tests
    logger.info("Starting component tests...")
    
    # Test Gmail connection
    if not test_gmail_connection():
        logger.error("Gmail connection test failed")
        return False
    
    # Test LLM components
    if not test_llm_components():
        logger.error("LLM components test failed")
        return False
    
    logger.info("All tests completed successfully!")
    return True

if __name__ == "__main__":
    main() 