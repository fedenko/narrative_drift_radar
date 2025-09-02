from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
import requests
from articles.models import Article
import environ

env = environ.Env()


class Command(BaseCommand):
    help = 'Fetch articles from NewsData.io API'
    
    def add_arguments(self, parser):
        parser.add_argument('--query', type=str, default='technology AI', help='Search query')
        parser.add_argument('--language', type=str, default='en', help='Language code')
        parser.add_argument('--limit', type=int, default=50, help='Number of articles to fetch')
    
    def handle(self, *args, **options):
        api_key = env('NEWSDATA_API_KEY', default=None)
        if not api_key:
            self.stdout.write(
                self.style.ERROR('NEWSDATA_API_KEY environment variable not set')
            )
            return
        
        url = 'https://newsdata.io/api/1/news'
        params = {
            'apikey': api_key,
            'q': options['query'],
            'language': options['language'],
            'size': min(options['limit'], 10)
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] != 'success':
                self.stdout.write(
                    self.style.ERROR(f"API error: {data.get('message', 'Unknown error')}")
                )
                return
            
            articles_created = 0
            for article_data in data.get('results', []):
                if not article_data.get('title') or not article_data.get('link'):
                    continue
                
                try:
                    article, created = Article.objects.get_or_create(
                        url=article_data['link'],
                        defaults={
                            'title': article_data['title'][:500],
                            'content': article_data.get('content', '') or article_data.get('description', ''),
                            'source': article_data.get('source_id', 'unknown'),
                            'published_date': timezone.now()
                        }
                    )
                    
                    if created:
                        articles_created += 1
                        self.stdout.write(f"Created: {article.title[:50]}...")
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Failed to create article: {str(e)}")
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully fetched {articles_created} new articles')
            )
            
        except requests.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'API request failed: {str(e)}')
            )