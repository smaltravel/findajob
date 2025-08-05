# Simplified Job Viewer Webapp

A simple web application to view AI-processed job opportunities from the `processed_jobs` database table.

## Features

- **Simple Job List**: View all processed jobs in a clean tile format
- **Job Details Modal**: Click on any job tile to see full details including:
  - Job overview (company, location, employment type, etc.)
  - AI-generated job summary
  - Original job description
  - AI-generated cover letter
  - External links to job posting and company profile
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **No Complex Pipeline**: Simple, focused interface without workflow management

## Prerequisites

- Node.js (v14 or higher) - OR Docker
- SQLite database with `processed_jobs` and `jobs` tables
- Processed jobs data in the database

## Quick Start with Docker

1. **Build and run with Docker Compose:**
```bash
docker-compose up --build
```

2. **Open your browser and navigate to:**
```
http://localhost:3000
```

3. **To stop the application:**
```bash
docker-compose down
```

## Manual Installation

1. Install dependencies:
```bash
npm install
```

2. Build the Vue application:
```bash
npm run build
```

## Running the Application

1. Start the server:
```bash
npm start
```

2. Open your browser and navigate to:
```
http://localhost:3000
```

## Development

For development with hot reload:

1. Start the development server:
```bash
npm run dev
```

2. In another terminal, start the backend server:
```bash
npm run dev:server
```

## Database Schema

The application expects the following database structure:

### `jobs` table
- Contains raw job data from LinkedIn scraping
- Fields: id, job_title, job_location, job_url, job_description, employer, etc.

### `processed_jobs` table
- Contains AI-processed job data
- Fields: id, job_id (FK to jobs), runid, cover_letter, job_summary, processing_status, etc.

## API Endpoints

- `GET /api/processed-jobs` - Get all processed jobs
- `GET /api/processed-jobs/:id` - Get specific processed job details

## Architecture

- **Frontend**: Vue 3 with Tailwind CSS
- **Backend**: Node.js/Express server
- **Database**: SQLite
- **Build Tool**: Vite

## File Structure

```
webapp/
├── src/
│   ├── components/
│   │   └── ProcessedJobsList.vue    # Main job listing component
│   ├── App.vue                      # Root component
│   └── main.js                      # Vue app entry point
├── server.js                        # Express server
├── package.json                     # Dependencies and scripts
├── Dockerfile                       # Docker configuration
├── docker-compose.yml               # Docker Compose configuration
└── jobs.db                          # SQLite database
```

## Docker Configuration

The application includes Docker support for easy deployment:

- **Dockerfile**: Multi-stage build for optimized production image
- **docker-compose.yml**: Complete setup with volume mounting for database
- **Health checks**: Automatic health monitoring
- **Volume mounting**: Database file persists between container restarts

### Docker Commands

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop and remove containers
docker-compose down

# Rebuild without cache
docker-compose build --no-cache
```

## Notes

- This is a simplified version that focuses only on viewing processed jobs
- No CV generation or complex workflow management
- Jobs must be pre-processed using the `job_processor.py` tool
- Only shows jobs with `processing_status = 'completed'`
- Database file is mounted as a volume in Docker for persistence
