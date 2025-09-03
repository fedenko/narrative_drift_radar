from django.core.management.base import BaseCommand
from django.conf import settings
import google.generativeai as genai
import numpy as np
import time
from articles.models import Article


class Command(BaseCommand):
    help = 'Process embeddings for articles using Google AI'
    
    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing')
        parser.add_argument('--limit', type=int, help='Limit number of articles to process (for testing)')
        parser.add_argument('--delay', type=float, default=0.1, help='Delay between requests to avoid rate limiting')
    
    def handle(self, *args, **options):
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            self.stdout.write(
                self.style.ERROR('GOOGLE_API_KEY not configured in settings')
            )
            return
        
        genai.configure(api_key=api_key)
        
        articles_without_embeddings = Article.objects.filter(embedding__isnull=True).order_by('-published_date')
        
        # Apply limit if specified
        if options['limit']:
            articles_without_embeddings = articles_without_embeddings[:options['limit']]
        
        total_articles = articles_without_embeddings.count()
        
        if total_articles == 0:
            self.stdout.write(self.style.SUCCESS('All articles already have embeddings'))
            return
        
        self.stdout.write(f'Processing embeddings for {total_articles} articles...')
        
        # Show sample of Ukrainian content
        sample_article = articles_without_embeddings.first()
        if sample_article:
            sample_text = sample_article.title[:100]
            self.stdout.write(f'Sample article title: {sample_text}...')
            ukrainian_chars = sum(1 for c in sample_text if c in 'іїєґІЇЄҐ')
            self.stdout.write(f'Ukrainian characters detected: {ukrainian_chars > 0}')
        
        batch_size = options['batch_size']
        delay = options['delay']
        processed = 0
        failed = 0
        
        for i in range(0, total_articles, batch_size):
            batch = articles_without_embeddings[i:i+batch_size]
            
            self.stdout.write(f'Processing batch {i//batch_size + 1}/{(total_articles-1)//batch_size + 1}...')
            
            for article in batch:
                try:
                    # Prepare text for embedding, handle Ukrainian content properly
                    text_to_embed = f"{article.title}\n\n{article.content}"
                    
                    # Truncate to reasonable length for embedding API
                    if len(text_to_embed) > 8000:
                        # For Ukrainian text, be more conservative with truncation
                        text_to_embed = text_to_embed[:7000] + "..."
                    
                    result = genai.embed_content(
                        model="models/text-embedding-004",
                        content=text_to_embed,
                        task_type="semantic_similarity"
                    )
                    
                    embedding_vector = result['embedding']
                    
                    if len(embedding_vector) == 768:
                        article.embedding = embedding_vector
                        article.save()
                        processed += 1
                        
                        if processed % 100 == 0:
                            self.stdout.write(f"Progress: {processed}/{total_articles} articles processed")
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"Unexpected embedding dimension: {len(embedding_vector)}")
                        )
                        failed += 1
                    
                    # Add delay to respect rate limits
                    if delay > 0:
                        time.sleep(delay)
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Failed to process article {article.id}: {str(e)}")
                    )
                    failed += 1
                    
                    # Add longer delay on error
                    if "quota" in str(e).lower() or "rate" in str(e).lower():
                        self.stdout.write("Rate limit hit, waiting 5 seconds...")
                        time.sleep(5)
        
        self.stdout.write("="*60)
        self.stdout.write(
            self.style.SUCCESS(f'✅ Successfully processed embeddings for {processed} articles')
        )
        if failed > 0:
            self.stdout.write(
                self.style.WARNING(f'❌ Failed to process {failed} articles')
            )
        
        # Show final statistics
        total_with_embeddings = Article.objects.filter(embedding__isnull=False).count()
        total_all_articles = Article.objects.count()
        self.stdout.write(f"📊 Total articles with embeddings: {total_with_embeddings}/{total_all_articles}")
        self.stdout.write(f"📈 Embedding coverage: {total_with_embeddings/total_all_articles*100:.1f}%")