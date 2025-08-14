# Job Processing Tools

This directory contains tools for processing job records and generating CVs, cover letters, and job summaries using AI providers (Ollama or Google AI).

## Job Processor Script

The `job_processor.py` script reads job records from the database by runid, processes them with AI providers to generate:
- Professional CVs tailored to specific job positions
- Cover letters for job applications
- Concise job summaries

## Supported AI Providers

### Ollama (Local LLM)
- **Model**: Any model available in Ollama (e.g., `deepseek-r1:7b`, `llama3.2`)
- **Setup**: Requires Ollama to be running locally
- **Use Case**: Privacy-focused, offline processing

### Google AI (Cloud)
- **Model**: Google's Gemini models (e.g., `gemini-1.5-flash`, `gemini-1.5-pro`)
- **Setup**: Requires Google AI API key
- **Use Case**: High-quality, cloud-based processing

### Prerequisites

1. **AI Provider Setup**: 
   - For Ollama: Local LLM running (e.g., Ollama with llama3.2 model)
   - For Google AI: Google AI API key
2. **Database**: The script expects a SQLite database with job records
3. **Python Dependencies**: Install the required packages

### Installation

1. Install the required dependencies:
```bash
pip install -r tools/requirements.txt
```

2. Setup your chosen AI provider:

**For Ollama (Local LLM):**
```bash
# Install Ollama if you haven't already
curl -fsSL https://ollama.ai/install.sh | sh

# Pull and run a model
ollama pull deepseek-r1:7b
ollama serve
```

**For Google AI (Cloud):**
```bash
# Get your API key from Google AI Studio
# https://makersuite.google.com/app/apikey

# Set the API key as environment variable
export GOOGLE_AI_API_KEY='your-api-key-here'
```

### Usage

```bash
python tools/job_processor.py --runid <runid> [options]
```

#### Arguments

- `--runid`: **Required**. The run ID to process jobs for
- `--cv_json`: **Required**. Path to the user CV JSON file
- `--database`: Path to the SQLite database (default: `webapp/jobs.db`)
- `--provider`: AI provider to use (`ollama` or `google`, default: `ollama`)
- `--api_key`: API key for Google AI (required if provider is `google`)

#### Examples

Process all new jobs for runid "2024-01-15" using Ollama:
```bash
python tools/job_processor.py --runid "2024-01-15" --cv_json cv.json
```

Process jobs using Google AI:
```bash
python tools/job_processor.py --runid "2024-01-15" --cv_json cv.json --provider google --api_key "your-api-key"
```

Use a different database:
```bash
python tools/job_processor.py --runid "2024-01-15" --cv_json cv.json --database "/path/to/jobs.db"
```

### Output

The script creates:

1. **Database Records**: New records in the `processed_jobs` table with:
   - CV content (text)
   - Cover letter (text)
   - Job summary (text)
   - CV file path (DOCX format)
   - Processing status and error messages

2. **DOCX Files**: Professional CV documents saved in the `generated_cvs/` directory

### Database Schema

The script creates a `processed_jobs` table with the following structure:

```sql
CREATE TABLE processed_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    runid TEXT NOT NULL,
    cv_content TEXT,
    cv_file_path TEXT,
    cover_letter TEXT,
    job_summary TEXT,
    processing_status TEXT DEFAULT 'pending',
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs (id)
);
```

### Error Handling

The script includes comprehensive error handling:
- Database connection errors
- LLM API failures
- File creation errors
- Individual job processing failures

Failed jobs are marked with `processing_status = 'failed'` and include error messages for debugging.

### Logging

The script provides detailed logging output showing:
- Database connection status
- Number of jobs found for processing
- Progress updates for each job
- Success/failure status for each operation
- File creation confirmations

### Performance Considerations

- The script processes jobs sequentially to avoid overwhelming the AI API
- A 1-second delay is added between requests
- Large job descriptions are handled efficiently
- Database operations are optimized with proper indexing

## Example Usage

### Testing Google AI Provider

You can test the Google AI provider using the example script:

```bash
# Set your API key
export GOOGLE_AI_API_KEY='your-api-key-here'

# Run the example
python tools/example_google_ai.py
```

This will demonstrate how to use the Google AI provider to generate job descriptions and cover letters with sample data.

### Provider Comparison

| Feature | Ollama | Google AI |
|---------|--------|-----------|
| Setup | Local installation | API key only |
| Privacy | Full local control | Cloud-based |
| Model Quality | Varies by model | High quality |
| Cost | Free (local) | Pay per request |
| Speed | Depends on hardware | Fast cloud processing | 