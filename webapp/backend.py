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

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'jobs.db')

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
            'current_stage': 'searching'
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
            # Read results from database
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Get jobs from the latest crawl
                cursor.execute('''
                    SELECT * FROM jobs 
                    WHERE keywords = ? AND location = ? 
                    AND created_at >= datetime('now', '-1 hour')
                    ORDER BY created_at DESC
                ''', (keywords, location))
                
                jobs_data = []
                for row in cursor.fetchall():
                    job_dict = dict(row)
                    jobs_data.append(job_dict)
                
                conn.close()
                
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
        
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
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
        
        if status not in ['new', 'applied', 'rejected']:
            return jsonify({'error': 'Invalid status'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE jobs 
            SET status = ?, updated_at = CURRENT_TIMESTAMP 
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
        
        if status not in ['new', 'applied', 'rejected']:
            return jsonify({'error': 'Invalid status'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Use parameterized query for safety
        placeholders = ','.join(['?' for _ in job_ids])
        cursor.execute(f'''
            UPDATE jobs 
            SET status = ?, updated_at = CURRENT_TIMESTAMP 
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
            WHERE created_at >= datetime('now', '-1 day')
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

if __name__ == '__main__':
    app.run(debug=True, port=5000) 