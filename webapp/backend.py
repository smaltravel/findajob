from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import os
import sys
import tempfile
import threading
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Global variable to store job crawling status
crawling_status = {
    'is_running': False,
    'progress': 0,
    'message': '',
    'jobs_found': 0,
    'current_stage': 'idle'
}

def run_scrapy_spider(keywords, location):
    """Run the Scrapy spider with given parameters"""
    global crawling_status
    
    try:
        crawling_status.update({
            'is_running': True,
            'progress': 0,
            'message': 'Starting LinkedIn job search...',
            'jobs_found': 0,
            'current_stage': 'searching'
        })
        
        # Change to the findajob directory
        findajob_dir = os.path.join(os.path.dirname(__file__), '..', 'findajob')
        os.chdir(findajob_dir)
        
        # Create a temporary file for output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        # Run the Scrapy spider
        cmd = [
            sys.executable, '-m', 'scrapy', 'crawl', 'linkedin',
            '-a', f'keywords={keywords}',
            '-a', f'location={location}',
            '-s', f'FEED_FORMAT=json',
            '-s', f'FEED_URI={temp_filename}',
            '-s', 'LOG_LEVEL=INFO'
        ]
        
        crawling_status['message'] = 'Crawling LinkedIn for job listings...'
        crawling_status['progress'] = 25
        
        # Run the spider
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Monitor the process
        while process.poll() is None:
            time.sleep(1)
            if crawling_status['progress'] < 75:
                crawling_status['progress'] += 10
        
        # Get the output
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            # Read the results
            try:
                with open(temp_filename, 'r') as f:
                    jobs_data = []
                    for line in f:
                        if line.strip():
                            jobs_data.append(json.loads(line))
                
                crawling_status.update({
                    'is_running': False,
                    'progress': 100,
                    'message': f'Successfully found {len(jobs_data)} jobs',
                    'jobs_found': len(jobs_data),
                    'current_stage': 'completed',
                    'results': jobs_data
                })
                
            except Exception as e:
                crawling_status.update({
                    'is_running': False,
                    'progress': 100,
                    'message': f'Error reading results: {str(e)}',
                    'current_stage': 'error'
                })
        else:
            crawling_status.update({
                'is_running': False,
                'progress': 100,
                'message': f'Spider failed: {stderr}',
                'current_stage': 'error'
            })
        
        # Clean up temporary file
        try:
            os.unlink(temp_filename)
        except:
            pass
            
    except Exception as e:
        crawling_status.update({
            'is_running': False,
            'progress': 100,
            'message': f'Error running spider: {str(e)}',
            'current_stage': 'error'
        })

@app.route('/api/start-workflow', methods=['POST'])
def start_workflow():
    """Start the job crawling workflow"""
    global crawling_status
    
    data = request.get_json()
    keywords = data.get('keywords', '').strip()
    location = data.get('location', '').strip()
    
    # Validate inputs
    if not keywords:
        return jsonify({'error': 'Keywords are required'}), 400
    if not location:
        return jsonify({'error': 'Location is required'}), 400
    
    # Check if already running
    if crawling_status['is_running']:
        return jsonify({'error': 'Workflow is already running'}), 409
    
    # Start the crawling process in a separate thread
    thread = threading.Thread(
        target=run_scrapy_spider,
        args=(keywords, location)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'message': 'Workflow started successfully',
        'status': 'started'
    })

@app.route('/api/workflow-status', methods=['GET'])
def get_workflow_status():
    """Get the current status of the workflow"""
    return jsonify(crawling_status)

@app.route('/api/workflow-results', methods=['GET'])
def get_workflow_results():
    """Get the results of the completed workflow"""
    if crawling_status['current_stage'] == 'completed' and 'results' in crawling_status:
        return jsonify({
            'jobs': crawling_status['results'],
            'total': crawling_status['jobs_found']
        })
    else:
        return jsonify({'error': 'No results available'}), 404

@app.route('/api/reset-workflow', methods=['POST'])
def reset_workflow():
    """Reset the workflow status"""
    global crawling_status
    crawling_status = {
        'is_running': False,
        'progress': 0,
        'message': '',
        'jobs_found': 0,
        'current_stage': 'idle'
    }
    return jsonify({'message': 'Workflow reset successfully'})

if __name__ == '__main__':
    app.run(debug=True, port=5000) 