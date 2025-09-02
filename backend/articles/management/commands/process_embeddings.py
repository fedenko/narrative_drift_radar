from django.core.management.base import BaseCommand
from django.conf import settings
import google.generativeai as genai
import numpy as np
from articles.models import Article
import environ

env = environ.Env()


class Command(BaseCommand):
    help = 'Process embeddings for articles using Google AI'
    
    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing')
    
    def handle(self, *args, **options):
        api_key = env('GOOGLE_API_KEY', default=None)
        if not api_key:
            self.stdout.write(
                self.style.ERROR('GOOGLE_API_KEY environment variable not set')
            )
            return
        
        genai.configure(api_key=api_key)
        
        articles_without_embeddings = Article.objects.filter(embedding__isnull=True)
        total_articles = articles_without_embeddings.count()
        
        if total_articles == 0:
            self.stdout.write(self.style.SUCCESS('All articles already have embeddings'))
            return
        
        self.stdout.write(f'Processing embeddings for {total_articles} articles...')
        
        batch_size = options['batch_size']
        processed = 0
        
        for i in range(0, total_articles, batch_size):
            batch = articles_without_embeddings[i:i+batch_size]
            
            for article in batch:
                try:
                    text_to_embed = f"{article.title} {article.content}"[:8000]
                    
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
                        self.stdout.write(f"Processed: {article.title[:50]}...")
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"Unexpected embedding dimension: {len(embedding_vector)}")
                        )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Failed to process {article.title[:50]}...: {str(e)}")
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed embeddings for {processed} articles')
        )