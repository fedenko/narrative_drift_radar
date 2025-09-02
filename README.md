# Narrative Drift Radar

A Django + React application that tracks narrative shifts in real-time using AI-powered analysis.

## Features

- **Article Collection**: Automated fetching from NewsData.io API
- **Semantic Analysis**: Google text-embedding-004 for article embeddings
- **Narrative Clustering**: Machine learning-based narrative detection
- **Timeline Visualization**: React-based timeline of narrative events
- **Weekly Reports**: AI-generated analysis using Gemini Pro

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

3. **Run Django migrations**:
```bash
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

4. **Access the application**:
- Frontend: http://localhost:3000
- Django Admin: http://localhost:8000/admin
- API: http://localhost:8000/api/

## Management Commands

```bash
# Fetch articles
python manage.py fetch_articles --limit 50

# Process embeddings
python manage.py process_embeddings --batch-size 10

# Detect narrative shifts
python manage.py detect_narrative_shifts --days 7 --clusters 5

# Generate weekly reports
python manage.py generate_weekly_reports
```

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

- **Backend**: Django + Django REST Framework
- **Frontend**: React + Vite + Tailwind CSS
- **Database**: PostgreSQL with pgvector extension
- **AI**: Google Generative AI (Gemini Pro, text-embedding-004)
- **Clustering**: scikit-learn
- **Containerization**: Docker + Docker Compose