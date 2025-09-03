# Narrative Drift Radar

A Django + React application that tracks narrative shifts in real-time using AI-powered analysis, with comprehensive Ukrainian language support for processing Ukrainian news content.

## Features

- **Ukrainian Language Support**: Full stack configured for Ukrainian content processing
- **Language Switching**: Frontend supports Ukrainian (УК) and English (EN) interfaces
- **Article Collection**: Automated fetching from NewsData.io API
- **Semantic Analysis**: Google text-embedding-004 for Ukrainian and English article embeddings
- **Ukrainian NLP**: spaCy-based Ukrainian natural language processing
- **Cost-Efficient Clustering**: Optimized clustering with content compression
- **Narrative Quality Metrics**: Coherence scoring, source diversity, and duplicate detection
- **Historical Data Processing**: Batch processing pipeline for large datasets
- **Timeline Visualization**: React-based timeline with Ukrainian localization
- **Weekly Reports**: AI-generated analysis using Gemini models

## Quick Start

1. **Clone and setup environment**:
```bash
cd narrative_drift_radar
cp .env.example .env
# Edit .env with your API keys
```

2. **Start with Docker**:
```bash
docker-compose up --build
```

3. **Run Django migrations and setup Ukrainian NLP**:
```bash
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser

# Install Ukrainian spaCy model (for advanced NLP features)
docker-compose exec backend python -m pip install https://github.com/explosion/spacy-models/releases/download/uk_core_news_sm-3.7.0/uk_core_news_sm-3.7.0-py3-none-any.whl
```

4. **Access the application**:
- Frontend: http://localhost:3000
- Django Admin: http://localhost:8000/admin
- API: http://localhost:8000/api/

## Management Commands

### Article Processing
```bash
# Fetch articles from NewsData.io
docker-compose exec backend python manage.py fetch_articles --limit 50

# Generate embeddings for articles (supports Ukrainian content)
docker-compose exec backend python manage.py process_embeddings --batch-size 10 --delay 0.1

# Process large batches with limits (for testing)
docker-compose exec backend python manage.py process_embeddings --limit 1000 --batch-size 15
```

### Narrative Analysis
```bash
# Cost-efficient clustering for current data
docker-compose exec backend python manage.py cost_efficient_clustering --weeks 1 --clusters-per-week 6

# Process historical data (past 2 months)
docker-compose exec backend python manage.py process_historical_data --months 2 --clusters-per-week 6

# Dry run to see processing plan and cost estimates
docker-compose exec backend python manage.py process_historical_data --dry-run --months 1

# Extract statements from Ukrainian articles
docker-compose exec backend python manage.py extract_statements --limit 100

# Detect statement-based narratives
docker-compose exec backend python manage.py detect_statement_narratives --weeks 1
```

### Reports and Analysis
```bash
# Generate weekly reports
docker-compose exec backend python manage.py generate_weekly_reports
```

## Historical Data Processing

The system includes a cost-efficient pipeline for processing large volumes of historical Ukrainian news articles:

### Processing Pipeline
1. **Embedding Generation**: Creates vector embeddings for articles using Google's text-embedding-004
2. **Content Compression**: Reduces token usage through medoid detection and TextRank summarization
3. **Quality Clustering**: Groups articles using coherence thresholds and source diversity
4. **Ukrainian NLP**: Processes Ukrainian text with language-specific stop words and entity recognition

### Cost Optimization
- **Compressed Content**: Reduces LLM token usage by 60-80%
- **Smart Caching**: Avoids reprocessing similar content
- **Batch Processing**: Efficiently handles large datasets
- **Model Selection**: Uses appropriate models (Gemini Flash vs Pro) based on task complexity

### Usage Example
```bash
# Check what would be processed (no cost)
docker-compose exec backend python manage.py process_historical_data --dry-run --months 2

# Process 2 months of historical data
docker-compose exec backend python manage.py process_historical_data --months 2 --clusters-per-week 6 --coherence-threshold 0.5

# Process with lower requirements for testing
docker-compose exec backend python manage.py process_historical_data --months 1 --clusters-per-week 3 --min-sources 2
```

### Expected Costs (USD)
- **Embedding Generation**: ~$0.01-0.02 per 1,000 articles
- **Narrative Clustering**: ~$0.0005 per narrative created
- **Historical Processing**: ~$10-15 for 70,000 articles (full 2 months)

## Automated Scheduling

Install the crontab for automated processing:
```bash
crontab crontab
```

## API Endpoints

- `/api/articles/` - Article listings
- `/api/narratives/` - Active narratives
- `/api/timeline/` - Timeline events
- `/api/clusters/` - Narrative clusters
- `/api/reports/weekly/` - Weekly reports

## Technology Stack

### Backend
- **Framework**: Django + Django REST Framework
- **Database**: PostgreSQL with pgvector extension for vector storage
- **AI Models**: Google Generative AI (Gemini 1.5 Flash, Gemini 2.0 Flash, text-embedding-004)
- **Ukrainian NLP**: spaCy with uk_core_news_sm model
- **Machine Learning**: scikit-learn for clustering and similarity analysis
- **Content Processing**: Custom content compression with TextRank and medoid detection

### Frontend
- **Framework**: React + Vite
- **Styling**: Tailwind CSS
- **Internationalization**: react-i18next with Ukrainian and English support
- **Language Switching**: Dynamic locale switching with persistent user preference

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Task Processing**: Django management commands for batch processing
- **Caching**: Built-in LLM response caching for cost optimization

### Language Support
- **Primary**: Ukrainian (uk) with full NLP pipeline
- **Secondary**: English (en) with fallback processing
- **Features**: Language-specific stop words, entity recognition, date formatting

## Ukrainian Language Configuration

### Backend Configuration
The system is pre-configured for Ukrainian language processing:
- **Django Locale**: Set to 'uk' with Europe/Kyiv timezone
- **Language Files**: Ukrainian stop words and NLP patterns included
- **Content Processing**: Automatically detects and processes Ukrainian text
- **Quality Metrics**: Adapted for Ukrainian content characteristics

### Frontend Language Switching
Users can switch between Ukrainian and English interfaces:
- **Language Toggle**: УК/EN buttons in the header
- **Persistent Settings**: Language preference saved in localStorage
- **Localized Content**: All UI elements translated including dates and numbers
- **API Integration**: Maintains language context across frontend and backend

### NLP Model Setup
For advanced Ukrainian text processing:
```bash
# Install Ukrainian spaCy model
docker-compose exec backend python -m spacy download uk_core_news_sm

# Or install directly from GitHub
docker-compose exec backend python -m pip install https://github.com/explosion/spacy-models/releases/download/uk_core_news_sm-3.7.0/uk_core_news_sm-3.7.0-py3-none-any.whl
```

### Troubleshooting Ukrainian Setup

**Ukrainian characters not displaying properly:**
- Ensure your terminal supports UTF-8 encoding
- Check that LANG environment variable is set to a UTF-8 locale

**spaCy model not found error:**
- Install the Ukrainian model using the commands above
- Restart the Docker containers after installation

**Poor clustering results for Ukrainian text:**
- Ensure articles have embeddings: `process_embeddings` command
- Check coherence threshold (try lowering from 0.5 to 0.3)
- Verify minimum source requirements are appropriate for your dataset