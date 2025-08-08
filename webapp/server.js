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

// Database connection pool
let db = null;

// Initialize database connection
function initializeDb() {
    return new Promise((resolve, reject) => {
        db = new sqlite3.Database(DB_PATH, sqlite3.OPEN_READWRITE, (err) => {
            if (err) {
                console.error('Error opening database:', err.message);
                reject(err);
            } else {
                console.log('Connected to the SQLite database.');
                // Enable WAL mode for better concurrency
                db.run('PRAGMA journal_mode = WAL;', (err) => {
                    if (err) {
                        console.warn('Warning: Could not enable WAL mode:', err.message);
                    }
                });
                // Set busy timeout
                db.run('PRAGMA busy_timeout = 30000;', (err) => {
                    if (err) {
                        console.warn('Warning: Could not set busy timeout:', err.message);
                    }
                });
                resolve(db);
            }
        });
    });
}

// Get database connection
function getDb() {
    if (!db) {
        throw new Error('Database not initialized');
    }
    return db;
}

// Safe database query wrapper
function safeQuery(query, params = []) {
    return new Promise((resolve, reject) => {
        const database = getDb();
        database.all(query, params, (err, rows) => {
            if (err) {
                console.error('Database query error:', err);
                reject(err);
            } else {
                resolve(rows);
            }
        });
    });
}

// Safe database get wrapper
function safeGet(query, params = []) {
    return new Promise((resolve, reject) => {
        const database = getDb();
        database.get(query, params, (err, row) => {
            if (err) {
                console.error('Database get error:', err);
                reject(err);
            } else {
                resolve(row);
            }
        });
    });
}

// Safe database run wrapper
function safeRun(query, params = []) {
    return new Promise((resolve, reject) => {
        const database = getDb();
        database.run(query, params, function(err) {
            if (err) {
                console.error('Database run error:', err);
                reject(err);
            } else {
                resolve({ changes: this.changes, lastID: this.lastID });
            }
        });
    });
}

// Initialize database on startup
initializeDb().catch(err => {
    console.error('Failed to initialize database:', err);
    process.exit(1);
});

// Database recovery function
async function recoverDatabase() {
    try {
        console.log('Attempting database recovery...');
        
        // Check database integrity
        const integrityResult = await safeQuery('PRAGMA integrity_check;');
        console.log('Database integrity check result:', integrityResult);
        
        // Optimize database
        await safeRun('PRAGMA optimize;');
        console.log('Database optimization completed');
        
        // Vacuum database to reclaim space and fix corruption
        await safeRun('VACUUM;');
        console.log('Database vacuum completed');
        
        return true;
    } catch (err) {
        console.error('Database recovery failed:', err);
        return false;
    }
}

// Add recovery endpoint
app.post('/api/database/recover', async (req, res) => {
    try {
        const success = await recoverDatabase();
        if (success) {
            res.json({ message: 'Database recovery completed successfully' });
        } else {
            res.status(500).json({ error: 'Database recovery failed' });
        }
    } catch (err) {
        console.error('Recovery endpoint error:', err);
        res.status(500).json({ error: 'Recovery failed' });
    }
});

// Graceful shutdown
process.on('SIGINT', () => {
    if (db) {
        db.close((err) => {
            if (err) {
                console.error('Error closing database:', err.message);
            } else {
                console.log('Database connection closed.');
            }
            process.exit(0);
        });
    } else {
        process.exit(0);
    }
});

// API Routes
app.get('/api/processed-jobs', async (req, res) => {
    try {
        const {
            page = '1',
            pageSize = '30',
            status = '',
            seniority = '',
            employer = '',
            title = '',
            sortBy = 'created',
            order = 'desc',
        } = req.query;

        const pageNum = Math.max(1, parseInt(page, 10) || 1);
        const sizeNum = Math.min(100, Math.max(1, parseInt(pageSize, 10) || 30));
        const offset = (pageNum - 1) * sizeNum;

        const whereClauses = ["pj.processing_status = 'completed'"];
        const params = [];

        if (status) {
            whereClauses.push('j.status = ?');
            params.push(status);
        }
        if (seniority) {
            whereClauses.push('LOWER(j.seniority_level) = LOWER(?)');
            params.push(seniority);
        }
        if (employer) {
            whereClauses.push('LOWER(j.employer) LIKE LOWER(?)');
            params.push(`%${employer}%`);
        }
        if (title) {
            whereClauses.push('LOWER(j.job_title) LIKE LOWER(?)');
            params.push(`%${title}%`);
        }

        const whereSql = whereClauses.length ? `WHERE ${whereClauses.join(' AND ')}` : '';

        // Sorting mapping
        let orderBySql = 'ORDER BY pj.created_at DESC';
        const direction = (String(order).toLowerCase() === 'asc') ? 'ASC' : 'DESC';
        if (sortBy === 'status') {
            orderBySql = `ORDER BY CASE j.status
                WHEN 'new' THEN 1
                WHEN 'applied' THEN 2
                WHEN 'interview_scheduled' THEN 3
                WHEN 'interview_completed' THEN 4
                WHEN 'offer_received' THEN 5
                WHEN 'offer_accepted' THEN 6
                WHEN 'not_answered' THEN 7
                WHEN 'filter_rejected' THEN 8
                WHEN 'user_rejected' THEN 9
                WHEN 'employer_rejected' THEN 10
                WHEN 'offer_rejected' THEN 11
                ELSE 999
            END ${direction}`;
        } else if (sortBy === 'seniority') {
            orderBySql = `ORDER BY CASE LOWER(COALESCE(j.seniority_level,''))
                WHEN 'internship' THEN 1
                WHEN 'entry level' THEN 2
                WHEN 'associate' THEN 3
                WHEN 'mid-senior level' THEN 4
                WHEN 'director' THEN 5
                WHEN 'executive' THEN 6
                ELSE 999
            END ${direction}`;
        } else if (sortBy === 'title') {
            orderBySql = `ORDER BY LOWER(COALESCE(j.job_title,'')) ${direction}`;
        } else if (sortBy === 'employer') {
            orderBySql = `ORDER BY LOWER(COALESCE(j.employer,'')) ${direction}`;
        } else if (sortBy === 'created') {
            orderBySql = `ORDER BY pj.created_at ${direction}`;
        }

        const baseSelect = `
            FROM processed_jobs pj
            JOIN jobs j ON pj.job_id = j.id
            ${whereSql}
        `;

        const countQuery = `SELECT COUNT(*) as total ${baseSelect}`;
        const countRow = await safeGet(countQuery, params);
        const total = countRow?.total || 0;

        const dataQuery = `
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
            ${baseSelect}
            ${orderBySql}
            LIMIT ? OFFSET ?
        `;

        const rows = await safeQuery(dataQuery, [...params, sizeNum, offset]);
        res.json({ jobs: rows, total, page: pageNum, pageSize: sizeNum });
    } catch (err) {
        console.error('Database error:', err);
        res.status(500).json({ error: 'Database error' });
    }
});

app.get('/api/processed-jobs/:id', async (req, res) => {
    try {
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
        
        const row = await safeGet(query, [jobId]);
        if (!row) {
            res.status(404).json({ error: 'Job not found' });
        } else {
            res.json(row);
        }
    } catch (err) {
        console.error('Database error:', err);
        res.status(500).json({ error: 'Database error' });
    }
});

// Update job status endpoint
app.put('/api/processed-jobs/:id/status', async (req, res) => {
    try {
        const jobId = req.params.id;
        const { status } = req.body;
        
        // Validate status
        const validStatuses = [
            'new', 'applied', 'user_rejected', 'filter_rejected', 
            'interview_scheduled', 'interview_completed', 'offer_received', 
            'offer_accepted', 'offer_rejected', 'not_answered', 'employer_rejected'
        ];
        
        if (!validStatuses.includes(status)) {
            return res.status(400).json({ error: 'Invalid status' });
        }
        
        // First get the job_id from processed_jobs table
        const getJobQuery = `
            SELECT job_id FROM processed_jobs WHERE id = ?
        `;
        
        const row = await safeGet(getJobQuery, [jobId]);
        if (!row) {
            return res.status(404).json({ error: 'Job not found' });
        }
        
        // Update the status in the jobs table
        const updateQuery = `
            UPDATE jobs 
            SET status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        `;
        
        const result = await safeRun(updateQuery, [status, row.job_id]);
        if (result.changes === 0) {
            return res.status(404).json({ error: 'Job not found' });
        }
        
        res.json({ 
            message: 'Status updated successfully',
            job_id: row.job_id,
            new_status: status
        });
    } catch (err) {
        console.error('Database error:', err);
        res.status(500).json({ error: 'Database error' });
    }
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