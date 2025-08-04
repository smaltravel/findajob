# Job Application Manager

A Vue.js application with Scrapy integration for automated LinkedIn job crawling and application management, featuring a SQLite database for persistent job storage and Ollama AI for intelligent content generation.

## Features

- **Workflow Management**: Automated job search pipeline with real-time status updates
- **LinkedIn Integration**: Scrapy spider for crawling job listings from LinkedIn
- **SQLite Database**: Persistent storage of crawled jobs with full CRUD operations
- **AI-Powered Processing**: Ollama integration for intelligent job analysis and content generation
- **Application Management**: Track job applications with comprehensive status management
- **AI-Generated Content**: Automated CV and cover letter generation tailored to each job
- **Responsive Design**: Modern UI built with Vue.js and Tailwind CSS

## Prerequisites

- Node.js (v16 or higher)
- Python (v3.8 or higher)
- pip (Python package manager)
- Ollama (for AI processing) - [Install Ollama](https://ollama.ai/)

## Installation

1. **Install Node.js dependencies:**

   ```bash
   npm install
   ```

2. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install Scrapy project dependencies:**

   ```bash
   cd ../findajob
   pip install -r requirements.txt
   ```

4. **Install and configure Ollama:**

   ```bash
   # Install Ollama (follow instructions at https://ollama.ai/)
   # Pull a model (e.g., llama3.2)
   ollama pull llama3.2
   ```

## Running the Application

### Development Mode

1. **Start Ollama (required for AI processing):**

   ```bash
   ollama serve
   ```

2. **Start the Flask backend API:**

   ```bash
   npm run backend
   ```

   This will start the Flask server on `http://localhost:5000` and automatically create the SQLite database

3. **Start the Vue.js frontend:**

   ```bash
   npm run dev
   ```

   This will start the Vite development server on `http://localhost:8080`

4. **Open your browser** and navigate to `http://localhost:8080`

### Production Build

1. **Build the frontend:**

   ```bash
   npm run build
   ```

2. **Start the backend:**

   ```bash
   python backend.py
   ```

## Database

The application uses SQLite for persistent job storage. The database file (`jobs.db`) is automatically created in the webapp directory when you first run the backend.

### Database Schema

```sql
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE,
    job_title TEXT,
    job_location TEXT,
    job_url TEXT,
    job_description TEXT,
    employer TEXT,
    employer_url TEXT,
    employment_type TEXT,
    job_function TEXT,
    seniority_level TEXT,
    industries TEXT,
    status TEXT NOT NULL CHECK (status IN ('new', 'user_rejected', 'filter_rejected', 'applied', 'interview_scheduled', 'interview_completed', 'offer_received', 'offer_accepted', 'offer_rejected', 'not_answered', 'employer_rejected')),
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_modified DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Database Features

- **Automatic Creation**: Database and tables are created automatically on first run
- **Indexed Queries**: Optimized for fast job retrieval and status filtering
- **Duplicate Prevention**: Jobs are deduplicated based on LinkedIn job ID
- **Status Management**: Track application status with comprehensive workflow states
- **Timestamps**: Automatic creation and update timestamps

## Pipeline Workflow

The application implements a 4-stage pipeline for job processing:

### Stage 1: Job Search
- Crawls LinkedIn for job listings using Scrapy
- Extracts job details and metadata
- Stores jobs in SQLite database

### Stage 2: Data Collection & Filtering
- Gathers jobs from database with status 'new'
- Filters and prepares data for AI processing
- Validates job data integrity

### Stage 3: AI Processing (Ollama)
- Sends job data to Ollama AI for analysis
- Generates short job descriptions
- Creates updated CV sections tailored to each job
- Generates personalized cover letters

### Stage 4: Application Tile Generation
- Combines job data with AI-generated content
- Creates application tiles for the frontend
- Makes jobs available for user interaction

## Usage

### Starting a Job Search Workflow

1. **Enter Keywords**: Type job keywords (e.g., "Python Developer", "React")
2. **Enter Location**: Specify the location (e.g., "San Francisco, CA")
3. **Click "Start Workflow"**: The system will begin the 4-stage pipeline

### Workflow Stages

The application shows real-time progress through these stages:

1. **Job Search**: Crawling LinkedIn for job listings
2. **Data Collection**: Gathering and filtering job data
3. **Data Processing**: Processing with AI (Ollama)
4. **Data Analysis**: Analyzing and preparing data
5. **Results Export**: Generating application tiles

### Managing Applications

- **View Jobs**: Click on any job tile to see detailed information
- **Apply/Reject**: Use the modal dialog to apply or reject jobs
- **Bulk Actions**: Select multiple jobs for bulk operations
- **Sorting**: Sort jobs by title, employer, or status
- **Status Tracking**: Track applications through comprehensive workflow states

## API Endpoints

### Workflow Management

- `POST /api/start-workflow`: Start the job crawling workflow
- `GET /api/workflow-status`: Get current workflow status
- `GET /api/workflow-results`: Get crawled job results
- `POST /api/reset-workflow`: Reset workflow status

### Job Management

- `GET /api/jobs`: Get all jobs with optional filtering
- `GET /api/jobs/{id}`: Get a specific job by ID
- `PUT /api/jobs/{id}/status`: Update job status
- `DELETE /api/jobs/{id}`: Delete a job
- `PUT /api/jobs/bulk-update`: Bulk update job statuses
- `DELETE /api/jobs/bulk-delete`: Bulk delete jobs
- `GET /api/stats`: Get job statistics

### AI Integration

- `GET /api/ollama-status`: Check Ollama service status

### Query Parameters

- `status`: Filter by job status (new, applied, rejected, etc.)
- `limit`: Number of jobs to return (default: 100)
- `offset`: Pagination offset (default: 0)

## Project Structure

```text
webapp/
├── src/
│   ├── components/
│   │   ├── WorkflowSection.vue    # Workflow management
│   │   ├── ApplicationsSection.vue # Job applications
│   │   └── JobModal.vue           # Job details modal
│   ├── App.vue                    # Main application
│   └── main.js                    # Vue app entry point
├── backend.py                     # Flask API server
├── jobs.db                        # SQLite database (auto-created)
├── requirements.txt               # Python dependencies
└── package.json                   # Node.js dependencies
```

## Scrapy Integration

The application integrates with a Scrapy spider located in `../findajob/spiders/linkedin_api_spider.py` that:

- Crawls LinkedIn job listings based on keywords and location
- Extracts job details including title, employer, description, and requirements
- Stores data directly in the SQLite database via the DatabasePipeline
- Handles duplicate prevention and data cleaning

### Database Pipeline Features

- **Automatic Storage**: Jobs are automatically saved to the database
- **Duplicate Prevention**: Prevents storing the same job multiple times
- **Status Management**: Sets initial status as 'new'
- **Performance Indexing**: Creates indexes for fast queries

## AI Integration (Ollama)

The application integrates with Ollama for intelligent job processing:

### AI Features

- **Job Analysis**: Analyzes job descriptions and requirements
- **Content Generation**: Creates tailored CV sections and cover letters
- **Smart Summaries**: Generates concise job descriptions
- **Personalization**: Adapts content to specific job requirements

### Ollama Configuration

- **Model**: Uses `llama3.2` by default (configurable in `backend.py`)
- **API Endpoint**: `http://localhost:11434`
- **Timeout**: 30 seconds per job processing
- **Error Handling**: Graceful fallback if AI processing fails

### Supported Models

Any Ollama model can be used by changing the `OLLAMA_MODEL` variable in `backend.py`:
- llama3.2
- llama3.1
- codellama
- mistral
- gemma

## Data Flow

1. User enters keywords and location
2. Frontend validates inputs and calls API
3. Backend starts Scrapy spider with parameters
4. Spider crawls LinkedIn and saves results to SQLite database
5. Backend processes pipeline stages:
   - Gathers and filters new jobs
   - Sends jobs to Ollama for AI processing
   - Generates application tiles with AI content
6. Frontend polls status and updates UI
7. When complete, application tiles are displayed
8. Users can manage jobs with full CRUD operations

## Troubleshooting

### Common Issues

1. **Database not created**: Ensure the backend has write permissions in the webapp directory
2. **Backend not starting**: Ensure Python dependencies are installed
3. **Scrapy errors**: Check that the findajob directory exists and has proper Scrapy setup
4. **CORS errors**: Ensure the Flask-CORS extension is properly installed
5. **Port conflicts**: Change ports in `backend.py` if port 5000 is in use
6. **Ollama not responding**: Ensure Ollama is running and accessible at `http://localhost:11434`

### Database Issues

1. **Database locked**: Ensure no other process is accessing the database
2. **Permission errors**: Check file permissions for the webapp directory
3. **Corrupted database**: Delete `jobs.db` and restart the backend to recreate it

### AI Processing Issues

1. **Ollama not running**: Start Ollama with `ollama serve`
2. **Model not found**: Pull the required model with `ollama pull llama3.2`
3. **Processing timeout**: Increase timeout in `backend.py` or use a faster model
4. **API errors**: Check Ollama logs and ensure the model is loaded

### Debug Mode

To run in debug mode, set the `FLASK_ENV` environment variable:

```bash
export FLASK_ENV=development
python backend.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
