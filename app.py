from flask import Flask, request, jsonify, render_template
import os
import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

FIBERY_API_TOKEN = os.environ.get("FIBERY_API_TOKEN")
FIBERY_WORKSPACE = os.environ.get("FIBERY_WORKSPACE")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = "video-analysis-system"
GITHUB_OWNER = "juliakriv0137"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/webhook/fibery/test', methods=['GET'])
def test_fibery_integration():
    """Test endpoint to verify Fibery integration"""
    try:
        # Check if we have all required environment variables
        required_vars = {
            'FIBERY_API_TOKEN': FIBERY_API_TOKEN,
            'FIBERY_WORKSPACE': FIBERY_WORKSPACE,
            'GITHUB_TOKEN': GITHUB_TOKEN
        }

        missing_vars = [k for k, v in required_vars.items() if not v]
        if missing_vars:
            return jsonify({
                'status': 'error',
                'message': 'Missing required environment variables',
                'missing': missing_vars
            }), 400

        # Test GitHub Actions API access
        github_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
        github_headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        github_response = requests.get(github_url, headers=github_headers)
        github_response.raise_for_status()

        # Test Fibery API access
        fibery_url = f"https://{FIBERY_WORKSPACE}.fibery.io/api/tokens/validate"
        fibery_headers = {
            'Authorization': f'Token {FIBERY_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        fibery_response = requests.get(fibery_url, headers=fibery_headers)
        fibery_response.raise_for_status()

        return jsonify({
            'status': 'success',
            'message': 'Integration test passed',
            'github_status': 'Connected',
            'fibery_status': 'Connected'
        }), 200

    except requests.exceptions.RequestException as e:
        logger.error(f"Integration test failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Integration test failed',
            'error': str(e)
        }), 500

@app.route('/webhook/fibery', methods=['POST'])
def fibery_webhook():
    """Handle incoming webhooks from Fibery"""
    try:
        logger.info("Received webhook from Fibery")
        data = request.json
        logger.debug(f"Webhook payload: {json.dumps(data, indent=2)}")

        # Validate request data
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data received',
                'code': 'EMPTY_PAYLOAD'
            }), 400

        # Validate action type
        action = data.get('action', {})
        if action.get('type') != 'Button Click':
            return jsonify({
                'status': 'error',
                'message': 'Unsupported webhook type. Only Button Click actions are supported.',
                'code': 'INVALID_ACTION_TYPE'
            }), 400

        # Validate entity data
        entity = data.get('entity', {})
        if not entity:
            return jsonify({
                'status': 'error',
                'message': 'No entity data provided',
                'code': 'MISSING_ENTITY'
            }), 400

        # Extract required fields
        video_url = entity.get('Video URL')
        entity_id = entity.get('fibery/id')

        # Validate required fields
        if not video_url:
            return jsonify({
                'status': 'error',
                'message': 'No video URL found in entity. Please add a video URL before analysis.',
                'code': 'MISSING_VIDEO_URL'
            }), 400

        if not entity_id:
            return jsonify({
                'status': 'error',
                'message': 'No entity ID found',
                'code': 'MISSING_ENTITY_ID'
            }), 400

        logger.info(f"Processing video URL: {video_url} for entity: {entity_id}")

        # Trigger GitHub Actions workflow
        try:
            trigger_github_analysis(video_url, entity_id)
            logger.info("Successfully triggered GitHub Actions workflow")

            return jsonify({
                'status': 'success',
                'message': 'Analysis started successfully',
                'details': {
                    'entity_id': entity_id,
                    'video_url': video_url,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }), 200

        except Exception as e:
            logger.error(f"Failed to trigger GitHub workflow: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to start video analysis',
                'code': 'WORKFLOW_TRIGGER_FAILED',
                'details': str(e)
            }), 500

    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'code': 'INTERNAL_ERROR',
            'details': str(e)
        }), 500

def trigger_github_analysis(video_url, fibery_id):
    """Trigger GitHub Actions workflow for video analysis"""
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/analyze-video.yml/dispatches"

    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    data = {
        'ref': 'main',
        'inputs': {
            'video_url': video_url,
            'fibery_id': fibery_id
        }
    }

    logger.debug(f"Triggering GitHub workflow with data: {json.dumps(data, indent=2)}")
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def update_fibery_entity(entity_id, analysis_results):
    """Update Fibery entity with analysis results"""
    url = f"https://api.fibery.io/{FIBERY_WORKSPACE}/api/commands"

    headers = {
        'Authorization': f'Token {FIBERY_API_TOKEN}',
        'Content-Type': 'application/json'
    }

    data = {
        'command': 'fibery.entity/update',
        'args': {
            'type': 'Video',
            'entity': {
                'fibery/id': entity_id,
                'Analysis Results': json.dumps(analysis_results, ensure_ascii=False)
            }
        }
    }

    logger.debug(f"Updating Fibery entity with data: {json.dumps(data, indent=2)}")
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)