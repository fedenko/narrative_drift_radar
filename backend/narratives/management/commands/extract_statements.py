from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from langchain_google_genai import GoogleGenerativeAI
import json
import time
from articles.models import Article
from narratives.models import Statement


class Command(BaseCommand):
    help = 'Extract statements from articles using LLM (who → what → why → consequence format)'
    
    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=5, help='Number of articles to process at once')
        parser.add_argument('--limit', type=int, help='Maximum number of articles to process')
        parser.add_argument('--skip-existing', action='store_true', help='Skip articles that already have statements')
    
    def extract_statements_from_article(self, article):
        """Extract structured statements from article using LLM."""
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            self.stdout.write(
                self.style.ERROR("GOOGLE_API_KEY not configured")
            )
            return []
        
        try:
            llm = GoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=api_key)
            
            # Create prompt for statement extraction
            prompt = f"""Analyze the following news article and extract key statements in the format: WHO → WHAT → WHY → CONSEQUENCE.

Article Title: {article.title}
Article Content: {article.content[:3000]}  # Limit content length
Source: {article.source}

Instructions:
1. Extract 1-3 most important statements/claims from the article
2. For each statement, identify:
   - WHO: The actor (person, organization, government, etc.)
   - WHAT: What they said, did, or what happened
   - WHY: The reasoning, cause, or motivation (if mentioned)
   - CONSEQUENCE: Expected or stated outcome/impact (if mentioned)

3. Return ONLY a JSON array with this exact structure:
[
  {{
    "actor": "WHO - clear identification of the actor",
    "action": "WHAT - the main action/statement/event",
    "reason": "WHY - reasoning or cause (empty string if not mentioned)",
    "consequence": "CONSEQUENCE - expected outcome (empty string if not mentioned)",
    "full_statement": "Complete extracted statement in natural language",
    "confidence": 0.8
  }}
]

Requirements:
- Be precise and factual
- Include direct quotes when available
- Confidence score from 0.0 to 1.0
- Maximum 3 statements per article
- Return empty array if no clear statements found
- Ensure valid JSON format

JSON Response:"""

            response = llm.invoke(prompt)
            
            # Parse JSON response
            try:
                # Clean response and extract JSON
                json_text = response.strip()
                if json_text.startswith('```json'):
                    json_text = json_text[7:]
                if json_text.endswith('```'):
                    json_text = json_text[:-3]
                
                statements_data = json.loads(json_text.strip())
                
                if not isinstance(statements_data, list):
                    self.stdout.write(
                        self.style.WARNING(f"Invalid JSON format for article {article.id}")
                    )
                    return []
                
                return statements_data
                
            except json.JSONDecodeError as e:
                self.stdout.write(
                    self.style.WARNING(f"JSON parsing error for article {article.id}: {str(e)}")
                )
                self.stdout.write(f"Raw response: {response[:200]}...")
                return []
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"LLM extraction failed for article {article.id}: {str(e)}")
            )
            return []
    
    def save_statements(self, article, statements_data):
        """Save extracted statements to database."""
        saved_count = 0
        
        for stmt_data in statements_data:
            try:
                # Validate required fields
                if not stmt_data.get('actor') or not stmt_data.get('action'):
                    continue
                
                statement = Statement(
                    article=article,
                    actor=stmt_data.get('actor', '')[:300],  # Truncate if too long
                    action=stmt_data.get('action', ''),
                    reason=stmt_data.get('reason', ''),
                    consequence=stmt_data.get('consequence', ''),
                    full_statement=stmt_data.get('full_statement', ''),
                    confidence_score=float(stmt_data.get('confidence', 0.0))
                )
                statement.save()
                saved_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Failed to save statement: {str(e)}")
                )
        
        return saved_count
    
    def handle(self, *args, **options):
        batch_size = options['batch_size']
        limit = options.get('limit')
        skip_existing = options['skip_existing']
        
        # Build queryset
        queryset = Article.objects.all().order_by('-created_at')
        
        if skip_existing:
            queryset = queryset.filter(statements__isnull=True).distinct()
        
        if limit:
            queryset = queryset[:limit]
        
        total_articles = queryset.count()
        if total_articles == 0:
            self.stdout.write(self.style.WARNING("No articles found to process"))
            return
        
        self.stdout.write(
            f"Processing {total_articles} articles in batches of {batch_size}"
        )
        
        processed = 0
        total_statements = 0
        
        # Process articles in batches
        for i in range(0, total_articles, batch_size):
            batch = list(queryset[i:i + batch_size])
            
            for article in batch:
                self.stdout.write(f"Processing article {processed + 1}/{total_articles}: {article.title[:50]}...")
                
                # Extract statements
                statements_data = self.extract_statements_from_article(article)
                
                if statements_data:
                    # Save to database
                    saved_count = self.save_statements(article, statements_data)
                    total_statements += saved_count
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"  → Extracted {saved_count} statements")
                    )
                else:
                    self.stdout.write("  → No statements extracted")
                
                processed += 1
                
                # Rate limiting - small delay between requests
                time.sleep(0.5)
            
            self.stdout.write(f"Batch {i//batch_size + 1} completed. Total statements: {total_statements}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted! Processed {processed} articles, extracted {total_statements} statements"
            )
        )