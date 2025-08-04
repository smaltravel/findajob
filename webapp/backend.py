from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import os
import sys
import tempfile
import threading
import time
import sqlite3
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Global variable to store job crawling status
crawling_status = {
    'is_running': False,
    'progress': 0,
    'message': '',
    'jobs_found': 0,
    'current_stage': 'idle',
    'pipeline_stage': 0
}

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'jobs.db')

# Ollama configuration
OLLAMA_BASE_URL = 'http://localhost:11434'
OLLAMA_MODEL = 'llama3.2'  # or your preferred model

def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def run_scrapy_spider(keywords, location):
    """Run the Scrapy spider with given parameters"""
    global crawling_status
    
    try:
        crawling_status.update({
            'is_running': True,
            'progress': 0,
            'message': 'Starting LinkedIn job search...',
            'jobs_found': 0,
            'current_stage': 'searching',
            'pipeline_stage': 1
        })
        
        # Change to the findajob directory
        findajob_dir = os.path.join(os.path.dirname(__file__), '..', 'findajob')
        os.chdir(findajob_dir)
        
        crawling_status['message'] = 'Crawling LinkedIn for job listings...'
        crawling_status['progress'] = 25
        
        # Run the Scrapy spider
        cmd = [
            sys.executable, '-m', 'scrapy', 'crawl', 'linkedin',
            '-a', f'keywords={keywords}',
            '-a', f'location={location}',
            '-s', 'LOG_LEVEL=INFO'
        ]
        
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
            crawling_status.update({
                'is_running': True,
                'progress': 100,
                'message': 'Job crawling completed. Starting data processing...',
                'current_stage': 'completed',
                'pipeline_stage': 1
            })
            
            # Start the next pipeline steps
            process_pipeline_steps(keywords, location)
            
        else:
            crawling_status.update({
                'is_running': False,
                'progress': 100,
                'message': f'Spider failed: {stderr}',
                'current_stage': 'error'
            })
            
    except Exception as e:
        crawling_status.update({
            'is_running': False,
            'progress': 100,
            'message': f'Error running spider: {str(e)}',
            'current_stage': 'error'
        })

def process_pipeline_steps(keywords, location):
    """Process the pipeline steps after crawling"""
    global crawling_status
    
    try:
        # Step 2: Gather and filter data
        crawling_status.update({
            'pipeline_stage': 2,
            'message': 'Gathering and filtering job data...',
            'progress': 0
        })
        
        new_jobs = gather_and_filter_jobs()
        
        if not new_jobs:
            crawling_status.update({
                'is_running': False,
                'message': 'No new jobs found to process.',
                'current_stage': 'completed'
            })
            return
        
        crawling_status.update({
            'jobs_found': len(new_jobs),
            'progress': 25,
            'message': f'Found {len(new_jobs)} new jobs. Processing with AI...'
        })
        
        # Step 3: Process with AI
        crawling_status.update({
            'pipeline_stage': 3,
            'message': 'Generating AI content for jobs...',
            'progress': 50
        })
        
        processed_jobs = process_jobs_with_ai(new_jobs)
        
        # Step 4: Generate application tiles
        crawling_status.update({
            'pipeline_stage': 4,
            'message': 'Generating application tiles...',
            'progress': 75
        })
        
        application_tiles = generate_application_tiles(processed_jobs)
        
        # Complete pipeline
        crawling_status.update({
            'is_running': False,
            'progress': 100,
            'message': f'Pipeline completed! Generated {len(application_tiles)} application tiles.',
            'current_stage': 'completed',
            'pipeline_stage': 4,
            'results': application_tiles
        })
        
    except Exception as e:
        crawling_status.update({
            'is_running': False,
            'progress': 100,
            'message': f'Pipeline error: {str(e)}',
            'current_stage': 'error'
        })

def gather_and_filter_jobs():
    """Step 2: Gather and filter jobs with status 'new'"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all jobs with status 'new'
        cursor.execute('''
            SELECT * FROM jobs 
            WHERE status = 'new'
            ORDER BY create_time DESC
        ''')
        
        jobs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jobs
        
    except Exception as e:
        print(f"Error gathering jobs: {e}")
        return []

def process_jobs_with_ai(jobs):
    """Step 3: Process jobs with Ollama AI"""
    processed_jobs = []
    
    for i, job in enumerate(jobs):
        try:
            # Update progress
            progress = 50 + (i / len(jobs)) * 25
            crawling_status.update({
                'progress': int(progress),
                'message': f'Processing job {i+1}/{len(jobs)} with AI...'
            })
            
            # Generate AI content
            ai_content = generate_ai_content(job)
            
            # Combine job data with AI content
            processed_job = {
                **job,
                'ai_short_description': ai_content.get('short_description', ''),
                'ai_updated_cv': ai_content.get('updated_cv', ''),
                'ai_cover_letter': ai_content.get('cover_letter', ''),
                'processed_at': datetime.now().isoformat()
            }
            
            processed_jobs.append(processed_job)
            
            # Small delay to avoid overwhelming the AI
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error processing job {job.get('id', 'unknown')}: {e}")
            # Continue with other jobs even if one fails
            continue
    
    return processed_jobs

def generate_ai_content(job):
    """Generate AI content for a job using Ollama"""
    try:
        # Prepare the prompt for the AI
        prompt = f"""
        Based on the following job posting, please provide:

        1. A short description (2-3 sentences) summarizing the key requirements and responsibilities
        2. An updated CV section highlighting relevant experience for this specific job
        3. A personalized cover letter

        Job Title: {job.get('job_title', 'Unknown')}
        Company: {job.get('employer', 'Unknown')}
        Location: {job.get('job_location', 'Unknown')}
        Employment Type: {job.get('employment_type', 'Unknown')}
        Seniority Level: {job.get('seniority_level', 'Unknown')}
        Job Function: {job.get('job_function', 'Unknown')}
        Industries: {job.get('industries', 'Unknown')}
        
        Job Description:
        {job.get('job_description', 'No description available')}

        Please format your response as JSON with the following structure:
        {{
            "short_description": "Brief summary of the job",
            "updated_cv": "Relevant CV section for this job",
            "cover_letter": "Personalized cover letter"
        }}
        """
        
        # Call Ollama API
        response = requests.post(
            f'{OLLAMA_BASE_URL}/api/generate',
            json={
                'model': OLLAMA_MODEL,
                'prompt': prompt,
                'stream': False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', '')
            
            # Try to parse JSON response
            try:
                # Extract JSON from the response (AI might include extra text)
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = ai_response[start_idx:end_idx]
                    ai_content = json.loads(json_str)
                    return ai_content
                else:
                    # Fallback if JSON parsing fails
                    return {
                        'short_description': ai_response[:200] + '...' if len(ai_response) > 200 else ai_response,
                        'updated_cv': 'CV section generated by AI',
                        'cover_letter': ai_response
                    }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    'short_description': ai_response[:200] + '...' if len(ai_response) > 200 else ai_response,
                    'updated_cv': 'CV section generated by AI',
                    'cover_letter': ai_response
                }
        else:
            print(f"Ollama API error: {response.status_code}")
            return {
                'short_description': 'AI processing failed',
                'updated_cv': 'CV section unavailable',
                'cover_letter': 'Cover letter unavailable'
            }
            
    except Exception as e:
        print(f"Error generating AI content: {e}")
        return {
            'short_description': 'AI processing failed',
            'updated_cv': 'CV section unavailable',
            'cover_letter': 'Cover letter unavailable'
        }

def generate_application_tiles(processed_jobs):
    """Step 4: Generate application tiles from processed jobs"""
    application_tiles = []
    
    for job in processed_jobs:
        tile = {
            'id': job.get('id'),
            'job_id': job.get('job_id'),
            'title': job.get('job_title'),
            'employer': job.get('employer'),
            'location': job.get('job_location'),
            'description': job.get('ai_short_description', job.get('job_description', '')),
            'status': 'new',
            'full_description': job.get('job_description'),
            'urls': [
                {
                    'name': 'LinkedIn Job Posting',
                    'url': job.get('job_url', '#')
                },
                {
                    'name': 'Company Profile',
                    'url': job.get('employer_url', '#')
                }
            ],
            'cv': job.get('ai_updated_cv', ''),
            'cover_letter': job.get('ai_cover_letter', ''),
            'employment_type': job.get('employment_type'),
            'seniority_level': job.get('seniority_level'),
            'job_function': job.get('job_function'),
            'industries': job.get('industries'),
            'created_at': job.get('create_time'),
            'processed_at': job.get('processed_at')
        }
        
        application_tiles.append(tile)
    
    return application_tiles

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
        'current_stage': 'idle',
        'pipeline_stage': 0
    }
    return jsonify({'message': 'Workflow reset successfully'})

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get all jobs from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get query parameters
        status = request.args.get('status')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = 'SELECT * FROM jobs WHERE 1=1'
        params = []
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        query += ' ORDER BY create_time DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        jobs = [dict(row) for row in cursor.fetchall()]
        
        # Get total count
        count_query = 'SELECT COUNT(*) FROM jobs WHERE 1=1'
        count_params = []
        if status:
            count_query += ' AND status = ?'
            count_params.append(status)
        
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'jobs': jobs,
            'total': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Get a specific job by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
        job = cursor.fetchone()
        
        conn.close()
        
        if job:
            return jsonify(dict(job))
        else:
            return jsonify({'error': 'Job not found'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/jobs/<int:job_id>/status', methods=['PUT'])
def update_job_status(job_id):
    """Update the status of a job"""
    try:
        data = request.get_json()
        status = data.get('status')
        
        valid_statuses = ['new', 'user_rejected', 'filter_rejected', 'applied', 'interview_scheduled', 
                         'interview_completed', 'offer_received', 'offer_accepted', 'offer_rejected', 
                         'not_answered', 'employer_rejected']
        
        if status not in valid_statuses:
            return jsonify({'error': 'Invalid status'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE jobs 
            SET status = ?, last_modified = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (status, job_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Job not found'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Status updated successfully'})
        
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a job"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Job not found'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Job deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/jobs/bulk-update', methods=['PUT'])
def bulk_update_jobs():
    """Bulk update job statuses"""
    try:
        data = request.get_json()
        job_ids = data.get('job_ids', [])
        status = data.get('status')
        
        if not job_ids:
            return jsonify({'error': 'No job IDs provided'}), 400
        
        valid_statuses = ['new', 'user_rejected', 'filter_rejected', 'applied', 'interview_scheduled', 
                         'interview_completed', 'offer_received', 'offer_accepted', 'offer_rejected', 
                         'not_answered', 'employer_rejected']
        
        if status not in valid_statuses:
            return jsonify({'error': 'Invalid status'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Use parameterized query for safety
        placeholders = ','.join(['?' for _ in job_ids])
        cursor.execute(f'''
            UPDATE jobs 
            SET status = ?, last_modified = CURRENT_TIMESTAMP 
            WHERE id IN ({placeholders})
        ''', [status] + job_ids)
        
        updated_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': f'Updated {updated_count} jobs successfully',
            'updated_count': updated_count
        })
        
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/jobs/bulk-delete', methods=['DELETE'])
def bulk_delete_jobs():
    """Bulk delete jobs"""
    try:
        data = request.get_json()
        job_ids = data.get('job_ids', [])
        
        if not job_ids:
            return jsonify({'error': 'No job IDs provided'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Use parameterized query for safety
        placeholders = ','.join(['?' for _ in job_ids])
        cursor.execute(f'DELETE FROM jobs WHERE id IN ({placeholders})', job_ids)
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': f'Deleted {deleted_count} jobs successfully',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get job statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get counts by status
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM jobs 
            GROUP BY status
        ''')
        status_counts = dict(cursor.fetchall())
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM jobs')
        total_count = cursor.fetchone()[0]
        
        # Get recent jobs count (last 24 hours)
        cursor.execute('''
            SELECT COUNT(*) FROM jobs 
            WHERE create_time >= datetime('now', '-1 day')
        ''')
        recent_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_jobs': total_count,
            'recent_jobs': recent_count,
            'by_status': status_counts
        })
        
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/ollama-status', methods=['GET'])
def check_ollama_status():
    """Check if Ollama is running and accessible"""
    try:
        response = requests.get(f'{OLLAMA_BASE_URL}/api/tags', timeout=5)
        if response.status_code == 200:
            return jsonify({
                'status': 'running',
                'models': response.json().get('models', [])
            })
        else:
            return jsonify({'status': 'error', 'message': 'Ollama not responding'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Ollama not accessible: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True, port=5000) 