const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'dist')));

// Database path
const DB_PATH = path.join(__dirname, 'jobs.db');

// Create database connection
function getDb() {
    return new sqlite3.Database(DB_PATH, (err) => {
        if (err) {
            console.error('Error opening database:', err.message);
        } else {
            console.log('Connected to the SQLite database.');
        }
    });
}

// API Routes
app.get('/api/processed-jobs', (req, res) => {
    const db = getDb();
    
    const query = `
        SELECT 
            pj.id,
            pj.job_id,
            pj.runid,
            pj.cover_letter,
            pj.job_summary,
            pj.processing_status,
            pj.created_at,
            pj.updated_at,
            j.job_title,
            j.job_location,
            j.job_url,
            j.job_description,
            j.employer,
            j.employer_url,
            j.employment_type,
            j.job_function,
            j.seniority_level,
            j.industries,
            j.status
        FROM processed_jobs pj
        JOIN jobs j ON pj.job_id = j.id
        WHERE pj.processing_status = 'completed'
        ORDER BY pj.created_at DESC
    `;
    
    db.all(query, [], (err, rows) => {
        if (err) {
            console.error('Database error:', err);
            res.status(500).json({ error: 'Database error' });
        } else {
            res.json({ jobs: rows });
        }
        db.close();
    });
});

app.get('/api/processed-jobs/:id', (req, res) => {
    const db = getDb();
    const jobId = req.params.id;
    
    const query = `
        SELECT 
            pj.id,
            pj.job_id,
            pj.runid,
            pj.cover_letter,
            pj.job_summary,
            pj.processing_status,
            pj.created_at,
            pj.updated_at,
            j.job_title,
            j.job_location,
            j.job_url,
            j.job_description,
            j.employer,
            j.employer_url,
            j.employment_type,
            j.job_function,
            j.seniority_level,
            j.industries,
            j.status
        FROM processed_jobs pj
        JOIN jobs j ON pj.job_id = j.id
        WHERE pj.id = ? AND pj.processing_status = 'completed'
    `;
    
    db.get(query, [jobId], (err, row) => {
        if (err) {
            console.error('Database error:', err);
            res.status(500).json({ error: 'Database error' });
        } else if (!row) {
            res.status(404).json({ error: 'Job not found' });
        } else {
            res.json(row);
        }
        db.close();
    });
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Serve the Vue app for all other routes
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://0.0.0.0:${PORT}`);
}); 