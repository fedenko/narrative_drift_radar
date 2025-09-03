from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.db.models import Count
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
import math
import hashlib
import json
from langchain_google_genai import GoogleGenerativeAI
from articles.models import Article
from narratives.models import Statement, Narrative, NarrativeCluster, TimelineEvent
from narratives.utils.content_compression import ContentCompressor


class Command(BaseCommand):
    help = 'Cost-efficient narrative detection using content compression and weekly batching'
    
    def add_arguments(self, parser):
        parser.add_argument('--weeks', type=int, default=1, help='Number of weeks to analyze')
        parser.add_argument('--clusters-per-week', type=int, default=8, help='Number of clusters per week')
        parser.add_argument('--min-sources', type=int, default=3, help='Minimum unique sources required')
        parser.add_argument('--min-articles', type=int, default=5, help='Minimum articles per cluster')
        parser.add_argument('--coherence-threshold', type=float, default=0.5, help='Minimum coherence score')
        parser.add_argument('--generate-weekly-brief', action='store_true', help='Generate weekly narrative brief')
    
    def __init__(self):
        super().__init__()
        self.compressor = ContentCompressor(language='uk')  # Ukrainian by default
        self.llm_calls = 0
        self.total_cost = 0.0
    
    def get_llm_model(self, task_type: str = 'naming'):
        """Get appropriate LLM model based on task type."""
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not configured")
        
        if task_type == 'naming':
            # Cheap model for simple naming tasks
            return GoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
        else:  # 'brief' or complex tasks
            # Better model for complex tasks
            return GoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
    
    def calculate_cost(self, task_type: str, token_count: int = 300):
        """Calculate approximate API cost."""
        if task_type == 'naming':
            # gemini-1.5-flash: ~$0.00015 per 1k tokens
            cost = (token_count / 1000) * 0.00015
        else:  # brief
            # gemini-2.5-flash: ~$0.001 per 1k tokens  
            cost = (token_count / 1000) * 0.001
        
        self.total_cost += cost
        return cost
    
    def check_content_cache(self, content_hash: str) -> dict:
        """Check if content has been processed before (simple in-memory cache for now)."""
        # TODO: Implement Redis cache
        return None
    
    def cache_content_result(self, content_hash: str, result: dict):
        """Cache processing result (simple in-memory for now)."""
        # TODO: Implement Redis cache
        pass
    
    def generate_cluster_name(self, compressed_content: dict, cluster_id: int) -> str:
        """Generate cluster name using cost-efficient LLM call."""
        content_hash = compressed_content.get('content_hash')
        
        # Check cache
        cached_result = self.check_content_cache(f"name_{content_hash}")
        if cached_result:
            return cached_result.get('name', f"Cluster {cluster_id}")
        
        try:
            llm = self.get_llm_model('naming')
            
            # Create compressed prompt
            prompt_content = self.compressor.create_llm_prompt_content(compressed_content)
            
            prompt = f"""Analyze the following news content and create a concise narrative name (2-4 words):

{prompt_content}

Generate a journalistic name that captures the main theme. Examples: "Climate Policy Debate", "Tech Regulation Update", "Economic Recovery Plans".

Name (2-4 words only):"""

            response = llm.invoke(prompt)
            narrative_name = response.strip().replace('"', '').replace("'", "")
            
            # Track cost
            self.llm_calls += 1
            self.calculate_cost('naming', len(prompt))
            
            # Cache result
            self.cache_content_result(f"name_{content_hash}", {'name': narrative_name})
            
            # Validate response
            if len(narrative_name.split()) <= 6 and len(narrative_name) <= 50:
                return narrative_name
            else:
                return f"News Cluster {cluster_id}"
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"Failed to generate name for cluster {cluster_id}: {str(e)}")
            )
            return f"News Cluster {cluster_id}"
    
    def generate_weekly_brief(self, week_narratives: list) -> str:
        """Generate weekly narrative summary using LLM."""
        if not week_narratives:
            return "No significant narratives detected this week."
        
        try:
            llm = self.get_llm_model('brief')
            
            # Create brief content from narratives
            narrative_summaries = []
            for narrative in week_narratives:
                narrative_summaries.append(
                    f"• {narrative.name} ({narrative.support_count} articles, "
                    f"{narrative.unique_sources_count} sources, "
                    f"coherence: {narrative.coherence_score:.2f})"
                )
            
            prompt = f"""Create a concise weekly news narrative summary:

Detected Narratives ({len(week_narratives)}):
{chr(10).join(narrative_summaries)}

Write a 2-3 sentence summary highlighting:
1. The main themes/topics that dominated the week
2. Any notable narrative shifts or emerging stories
3. Overall media focus trends

Weekly Summary:"""

            response = llm.invoke(prompt)
            
            # Track cost
            self.llm_calls += 1
            self.calculate_cost('brief', len(prompt) + len(response))
            
            return response.strip()
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"Failed to generate weekly brief: {str(e)}")
            )
            return f"Weekly analysis completed with {len(week_narratives)} narratives detected."
    
    def process_week_batch(self, start_date: datetime, end_date: datetime, 
                          clusters_per_week: int, min_sources: int, 
                          min_articles: int, coherence_threshold: float) -> list:
        """Process one week of articles into narratives."""
        
        self.stdout.write(f"Processing week: {start_date.date()} to {end_date.date()}")
        
        # Get articles for this week with embeddings
        week_articles = Article.objects.filter(
            published_date__gte=start_date,
            published_date__lt=end_date,
            embedding__isnull=False
        ).select_related()
        
        if week_articles.count() < clusters_per_week:
            self.stdout.write(f"  Not enough articles: {week_articles.count()}")
            return []
        
        self.stdout.write(f"  Found {week_articles.count()} articles")
        
        # Extract embeddings and articles
        articles = list(week_articles)
        embeddings = np.array([article.embedding for article in articles])
        
        # Perform clustering
        kmeans = KMeans(n_clusters=clusters_per_week, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # Calculate overall quality
        if len(embeddings) > clusters_per_week:
            silhouette_avg = silhouette_score(embeddings, cluster_labels)
            self.stdout.write(f"  Silhouette score: {silhouette_avg:.3f}")
        
        week_narratives = []
        
        # Process each cluster
        for cluster_id in range(clusters_per_week):
            cluster_indices = np.where(cluster_labels == cluster_id)[0]
            cluster_articles = [articles[i] for i in cluster_indices]
            cluster_embeddings = embeddings[cluster_indices]
            
            # Apply quality filters
            if len(cluster_articles) < min_articles:
                continue
            
            unique_sources = set(article.source for article in cluster_articles)
            if len(unique_sources) < min_sources:
                continue
            
            unique_dates = set(article.published_date.date() for article in cluster_articles)
            if len(unique_dates) < 2:  # At least 2 different days
                continue
            
            # Calculate coherence
            coherence_score = self.compressor.calculate_coherence_score(cluster_embeddings)
            if coherence_score < coherence_threshold:
                continue
            
            # Compress content for efficient LLM processing
            compressed_content = self.compressor.compress_cluster_content(
                cluster_articles, 
                cluster_embeddings,
                max_medoids=3,
                max_sentences=6,
                max_terms=12
            )
            
            # Generate narrative name using compressed content
            narrative_name = self.generate_cluster_name(compressed_content, cluster_id)
            
            # Calculate quality metrics
            source_diversity = self.calculate_source_diversity(cluster_articles)
            near_duplicate_rate = self.calculate_near_duplicate_rate(cluster_articles)
            
            # Create description
            description = f"Weekly narrative with {len(cluster_articles)} articles from {len(unique_sources)} sources. Compression: {compressed_content.get('compression_ratio', 0):.1%}"
            
            # Create narrative
            narrative, created = Narrative.objects.get_or_create(
                name=narrative_name,
                defaults={
                    'description': description,
                    'source_diversity_score': source_diversity,
                    'support_count': len(cluster_articles),
                    'unique_sources_count': len(unique_sources),
                    'coherence_score': coherence_score,
                    'near_duplicate_rate': near_duplicate_rate,
                    'persistence_days': len(unique_dates)
                }
            )
            
            if not created:
                # Update existing narrative
                narrative.source_diversity_score = source_diversity
                narrative.support_count = len(cluster_articles)
                narrative.unique_sources_count = len(unique_sources)
                narrative.coherence_score = coherence_score
                narrative.near_duplicate_rate = near_duplicate_rate
                narrative.persistence_days = len(unique_dates)
                narrative.save()
            
            # Create cluster
            cluster = NarrativeCluster.objects.create(
                narrative=narrative,
                cluster_date=start_date.date(),
                centroid=kmeans.cluster_centers_[cluster_id].tolist()
            )
            cluster.articles.add(*cluster_articles)
            
            # Create timeline event
            TimelineEvent.objects.create(
                narrative=narrative,
                event_type='emergence',
                description=f"Weekly narrative: {len(cluster_articles)} articles, coherence {coherence_score:.3f}",
                event_date=start_date,
                significance_score=coherence_score * source_diversity,
            )
            
            week_narratives.append(narrative)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ {narrative_name}: {len(cluster_articles)} articles, "
                    f"{len(unique_sources)} sources, coherence {coherence_score:.3f}"
                )
            )
        
        return week_narratives
    
    def calculate_source_diversity(self, articles):
        """Calculate source diversity using entropy."""
        sources = [article.source for article in articles]
        source_counts = Counter(sources)
        
        if len(source_counts) <= 1:
            return 0.0
        
        total = len(sources)
        entropy = 0.0
        for count in source_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        max_entropy = math.log2(len(source_counts))
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    def calculate_near_duplicate_rate(self, articles):
        """Calculate near-duplicate rate."""
        if len(articles) < 2:
            return 0.0
        
        embeddings = [article.embedding for article in articles if article.embedding is not None]
        if len(embeddings) < 2:
            return 0.0
        
        from sklearn.metrics.pairwise import cosine_similarity
        embeddings_array = np.array(embeddings)
        similarities = cosine_similarity(embeddings_array)
        
        high_similarity_count = 0
        total_pairs = 0
        
        for i in range(len(similarities)):
            for j in range(i + 1, len(similarities)):
                if similarities[i][j] > 0.95:
                    high_similarity_count += 1
                total_pairs += 1
        
        return high_similarity_count / total_pairs if total_pairs > 0 else 0.0
    
    def handle(self, *args, **options):
        weeks = options['weeks']
        clusters_per_week = options['clusters_per_week']
        min_sources = options['min_sources']
        min_articles = options['min_articles']
        coherence_threshold = options['coherence_threshold']
        generate_brief = options['generate_weekly_brief']
        
        self.stdout.write(f"Cost-efficient clustering: {weeks} weeks, {clusters_per_week} clusters/week")
        self.stdout.write(f"Quality filters: ≥{min_sources} sources, ≥{min_articles} articles, coherence ≥{coherence_threshold}")
        
        all_narratives = []
        
        # Process each week
        for week_num in range(weeks):
            end_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = end_date - timedelta(days=7 * (week_num + 1))
            end_date = end_date - timedelta(days=7 * week_num)
            
            week_narratives = self.process_week_batch(
                start_date, end_date, clusters_per_week, 
                min_sources, min_articles, coherence_threshold
            )
            
            all_narratives.extend(week_narratives)
            
            # Generate weekly brief if requested
            if generate_brief and week_narratives:
                brief = self.generate_weekly_brief(week_narratives)
                self.stdout.write(f"\\n📋 Week {week_num + 1} Brief:")
                self.stdout.write(f"   {brief}\\n")
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\\n✅ Completed! Created {len(all_narratives)} narratives "
                f"using {self.llm_calls} LLM calls (~${self.total_cost:.3f})"
            )
        )