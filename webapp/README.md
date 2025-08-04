# Job Application Manager

A Vue.js application with Scrapy integration for automated LinkedIn job crawling and application management.

## Features

- **Workflow Management**: Automated job search pipeline with real-time status updates
- **LinkedIn Integration**: Scrapy spider for crawling job listings from LinkedIn
- **Application Management**: Track job applications with status management
- **AI-Generated Content**: Automated CV and cover letter generation
- **Responsive Design**: Modern UI built with Vue.js and Tailwind CSS

## Prerequisites

- Node.js (v16 or higher)
- Python (v3.8 or higher)
- pip (Python package manager)

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

## Running the Application

### Development Mode

1. **Start the Flask backend API:**
   ```bash
   npm run backend
   ```
   This will start the Flask server on `http://localhost:5000`

2. **Start the Vue.js frontend:**
   ```bash
   npm run dev
   ```
   This will start the Vite development server on `http://localhost:5173`

3. **Open your browser** and navigate to `http://localhost:5173`

### Production Build

1. **Build the frontend:**
   ```bash
   npm run build
   ```

2. **Start the backend:**
   ```bash
   python backend.py
   ```

## Usage

### Starting a Job Search Workflow

1. **Enter Keywords**: Type job keywords (e.g., "Python Developer", "React")
2. **Enter Location**: Specify the location (e.g., "San Francisco, CA")
3. **Click "Start Workflow"**: The system will begin crawling LinkedIn for job listings

### Workflow Stages

The application shows real-time progress through these stages:
1. **Job Search**: Crawling LinkedIn for job listings
2. **Data Collection**: Collecting detailed job information
3. **Data Processing**: Processing and organizing the data
4. **Data Analysis**: Analyzing job requirements and descriptions
5. **Results Export**: Making jobs available in the applications section

### Managing Applications

- **View Jobs**: Click on any job tile to see detailed information
- **Apply/Reject**: Use the modal dialog to apply or reject jobs
- **Bulk Actions**: Select multiple jobs for bulk operations
- **Sorting**: Sort jobs by title, employer, or status
- **Status Tracking**: Track applications as New, Applied, or Rejected

## API Endpoints

- `POST /api/start-workflow`: Start the job crawling workflow
- `GET /api/workflow-status`: Get current workflow status
- `GET /api/workflow-results`: Get crawled job results
- `POST /api/reset-workflow`: Reset workflow status

## Project Structure

```
webapp/
├── src/
│   ├── components/
│   │   ├── WorkflowSection.vue    # Workflow management
│   │   ├── ApplicationsSection.vue # Job applications
│   │   └── JobModal.vue           # Job details modal
│   ├── App.vue                    # Main application
│   └── main.js                    # Vue app entry point
├── backend.py                     # Flask API server
├── requirements.txt               # Python dependencies
└── package.json                   # Node.js dependencies
```

## Scrapy Integration

The application integrates with a Scrapy spider located in `../findajob/spiders/linkedin_api_spider.py` that:

- Crawls LinkedIn job listings based on keywords and location
- Extracts job details including title, employer, description, and requirements
- Returns structured data for the frontend to process

## Troubleshooting

### Common Issues

1. **Backend not starting**: Ensure Python dependencies are installed
2. **Scrapy errors**: Check that the findajob directory exists and has proper Scrapy setup
3. **CORS errors**: Ensure the Flask-CORS extension is properly installed
4. **Port conflicts**: Change ports in `backend.py` if port 5000 is in use

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
