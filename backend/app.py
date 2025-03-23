from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from agent.agent import invoke_agent

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Configure CORS to allow all methods and headers
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/generate-digest', methods=['POST', 'OPTIONS'])
def generate_digest():
    if request.method == 'OPTIONS':
        # Handle preflight request
        return '', 204
        
    try:
        data = request.get_json()
        logger.info(f"Received request with data: {data}")
        
        email_count = data.get('emailCount', 10)  # Default to 10 if not specified
        logger.info(f"Processing request for {email_count} emails")
        
        # Invoke the agent to process emails and generate digest
        digest = invoke_agent(email_count)
        
        return jsonify({
            'status': 'success',
            'digest': digest
        })
    except Exception as e:
        logger.error(f"Error generating digest: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    logger.info("Starting Flask server...")
    app.run(debug=True, host='0.0.0.0', port=5000) 