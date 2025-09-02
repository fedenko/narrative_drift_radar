from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from dateutil import parser
from newsdataapi import NewsDataApiClient
from articles.models import Article


class Command(BaseCommand):
    help = 'Fetch articles from NewsData.io API'
    
    def add_arguments(self, parser):
        parser.add_argument('--language', type=str, default='en', help='Language code')
        parser.add_argument('--country', type=str, default='us', help='Country code')
        parser.add_argument('--category', type=str, default='politics', help='News category')
        parser.add_argument('--limit', type=int, default=50, help='Number of articles to fetch')
    
    def handle(self, *args, **options):
        api_key = settings.NEWSDATA_API_KEY
        if not api_key:
            self.stdout.write(
                self.style.ERROR('NEWSDATA_API_KEY environment variable not set')
            )
            return
        
        # Initialize NewsData API client
        api_client = NewsDataApiClient(apikey=api_key)
        
        articles_created = 0
        articles_processed = 0
        page = None
        
        try:
            while articles_processed < options['limit']:
                # Calculate remaining articles to fetch
                remaining = options['limit'] - articles_processed
                size = min(remaining, 10)  # API max is 10 per request
                
                # Fetch articles with pagination
                response = api_client.news_api(
                    q=None,  # No specific query
                    language=options['language'],
                    country=options['country'],
                    category=options['category'],
                    page=page,
                    size=size
                )
                
                # Process articles from response
                for article_data in response.get('results', []):
                    if not article_data.get('title') or not article_data.get('link'):
                        continue
                    
                    # Parse published date
                    published_date = timezone.now()
                    if article_data.get('pubDate'):
                        try:
                            parsed_date = parser.parse(article_data['pubDate'])
                            # Make timezone-aware if naive
                            if parsed_date.tzinfo is None:
                                published_date = timezone.make_aware(parsed_date)
                            else:
                                published_date = parsed_date
                        except (ValueError, TypeError):
                            published_date = timezone.now()
                    
                    try:
                        article, created = Article.objects.get_or_create(
                            url=article_data['link'],
                            defaults={
                                'title': article_data['title'][:500],
                                'content': article_data.get('content', '') or article_data.get('description', ''),
                                'source': article_data.get('source_id', 'unknown'),
                                'published_date': published_date
                            }
                        )
                        
                        if created:
                            articles_created += 1
                            self.stdout.write(f"Created: {article.title[:50]}...")
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f"Failed to create article: {str(e)}")
                        )
                
                articles_processed += len(response.get('results', []))
                
                # Check for next page
                page = response.get('nextPage')
                if not page or not response.get('results'):
                    break
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully fetched {articles_created} new articles')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'API request failed: {str(e)}')
            )
