# Findajob Project

Welcome to the Findajob project! An AI-powered job search assistant that helps you find and analyze job opportunities.

## Repository Structure

```text
findajob/
├── backend/                 # FastAPI backend with job processing and AI analysis
│   ├── app/                # Main application code
│   │   ├── core/          # Core functionality (LLM integration, spiders)
│   │   ├── models.py      # Database models
│   │   ├── routes/        # API endpoints
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # Business logic services
│   ├── Dockerfile         # Backend container configuration
│   └── requirements.txt   # Python dependencies
├── frontend/               # Single-page application (HTML/CSS/JS)
│   └── index.html         # Main dashboard interface
├── docker-compose.yml      # Multi-container setup configuration
├── nginx.conf             # Nginx reverse proxy configuration
└── schemas/               # Additional schema definitions
```

## Getting Started

### Prerequisites

1. **Install Docker and Docker Compose** (Required)

   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install docker.io docker-compose
   
   # macOS
   brew install docker docker-compose
   
   # Windows
   # Download Docker Desktop from https://www.docker.com/products/docker-desktop
   ```

2. **Install VS Code** (Recommended)
   - Download from [https://code.visualstudio.com/](https://code.visualstudio.com/)
   - Install Docker extension for better container management

### Setup Instructions

#### Option 1: Using VS Code (Recommended)

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/smaltravel/findajob.git
   cd findajob
   ```

2. **Open in VS Code:**

   ```bash
   code .
   ```

3. **Start the Application:**
   - Right-click on `docker-compose.yml` in VS Code
   - Select "Docker Compose: Up"
   - Wait for all services to start

#### Option 2: Using Shell Commands

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/smaltravel/findajob.git
   cd findajob
   ```

2. **Start the Application:**

   ```bash
   docker-compose up -d
   ```

3. **Check Status:**

   ```bash
   docker-compose ps
   ```

### Accessing the Application

Once all services are running:

- **Frontend Dashboard**: <http://localhost:80>
- **Backend API**: <http://localhost:8000>
- **API Documentation**: <http://localhost:8000/docs>

### Stopping the Application

#### VS Code

- Right-click on `docker-compose.yml`
- Select "Docker Compose: Down"

#### Shell

```bash
docker-compose down
```

## Features

- **AI-Powered Job Analysis**: Intelligent job matching using LLM models
- **Multi-Source Job Scraping**: LinkedIn and other job platforms
- **Smart CV Matching**: Background alignment scoring (0-100%)
- **Cover Letter Generation**: AI-generated personalized cover letters
- **Job Pipeline Management**: Automated job search workflows
- **Modern Web Interface**: Responsive dashboard with real-time updates

## Technology Stack

- **Backend**: FastAPI, Python, PostgreSQL
- **Frontend**: HTML5
- **AI**: Ollama (local) / Google Gemini (cloud)
- **Infrastructure**: Docker, Docker Compose, Nginx
- **Job Scraping**: Custom spiders with API integration

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
