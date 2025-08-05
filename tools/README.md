# Job Processing Tools

This directory contains tools for processing job records and generating CVs, cover letters, and job summaries using a local LLM.

## Job Processor Script

The `job_processor.py` script reads job records from the database by runid, processes them with a local LLM to generate:
- Professional CVs tailored to specific job positions
- Cover letters for job applications
- Concise job summaries

### Prerequisites

1. **Local LLM Setup**: You need a local LLM running (e.g., Ollama with llama3.2 model)
2. **Database**: The script expects a SQLite database with job records
3. **Python Dependencies**: Install the required packages

### Installation

1. Install the required dependencies:
```bash
pip install -r tools/requirements.txt
```

2. Make sure you have a local LLM running (e.g., Ollama):
```bash
# Install Ollama if you haven't already
curl -fsSL https://ollama.ai/install.sh | sh

# Pull and run the llama3.2 model
ollama pull llama3.2
ollama serve
```

### Usage

```bash
python tools/job_processor.py --runid <runid> [options]
```

#### Arguments

- `--runid`: **Required**. The run ID to process jobs for
- `--database`: Path to the SQLite database (default: `webapp/jobs.db`)
- `--llm-url`: URL of the local LLM API (default: `http://localhost:11434/api/generate`)
- `--model`: LLM model to use (default: `llama3.2`)

#### Examples

Process all new jobs for runid "2024-01-15":
```bash
python tools/job_processor.py --runid "2024-01-15"
```

Use a different database and LLM URL:
```bash
python tools/job_processor.py --runid "2024-01-15" --database "/path/to/jobs.db" --llm-url "http://localhost:8080/api/generate"
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

- The script processes jobs sequentially to avoid overwhelming the LLM API
- A 1-second delay is added between requests
- Large job descriptions are handled efficiently
- Database operations are optimized with proper indexing 