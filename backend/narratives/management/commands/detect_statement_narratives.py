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
from langchain_google_genai import GoogleGenerativeAI
from articles.models import Article
from narratives.models import Statement, Narrative, NarrativeCluster, TimelineEvent


class Command(BaseCommand):
    help = 'Detect narratives from statement clustering with quality metrics'
    
    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
        parser.add_argument('--clusters', type=int, default=5, help='Number of clusters')
        parser.add_argument('--min-sources', type=int, default=3, help='Minimum unique sources required')
        parser.add_argument('--min-statements', type=int, default=5, help='Minimum statements per narrative')
        parser.add_argument('--coherence-threshold', type=float, default=0.6, help='Minimum coherence score')
    
    def calculate_source_diversity(self, statements):
        """Calculate source diversity using entropy."""
        if not statements:
            return 0.0
        
        # Count statements per source
        sources = [stmt.article.source for stmt in statements]
        source_counts = Counter(sources)
        
        if len(source_counts) <= 1:
            return 0.0
        
        # Calculate entropy
        total = len(sources)
        entropy = 0.0
        for count in source_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        # Normalize by maximum possible entropy
        max_entropy = math.log2(len(source_counts))
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    def calculate_coherence_score(self, embeddings):
        """Calculate average cosine similarity within cluster."""
        if len(embeddings) < 2:
            return 0.0
        
        from sklearn.metrics.pairwise import cosine_similarity
        
        similarities = []
        embeddings_array = np.array(embeddings)
        
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                sim = cosine_similarity([embeddings_array[i]], [embeddings_array[j]])[0][0]
                similarities.append(sim)
        
        return np.mean(similarities) if similarities else 0.0
    
    def calculate_near_duplicate_rate(self, statements):
        """Calculate rate of near-duplicate statements."""
        if len(statements) < 2:
            return 0.0
        
        from sklearn.metrics.pairwise import cosine_similarity
        
        embeddings = [stmt.embedding for stmt in statements if stmt.embedding is not None]
        if len(embeddings) < 2:
            return 0.0
        
        embeddings_array = np.array(embeddings)
        similarities = cosine_similarity(embeddings_array)
        
        # Count pairs with similarity > 0.95 (excluding diagonal)
        high_similarity_count = 0
        total_pairs = 0
        
        for i in range(len(similarities)):
            for j in range(i + 1, len(similarities)):
                if similarities[i][j] > 0.95:
                    high_similarity_count += 1
                total_pairs += 1
        
        return high_similarity_count / total_pairs if total_pairs > 0 else 0.0
    
    def generate_narrative_name(self, cluster_statements, cluster_id):
        """Generate meaningful narrative name from clustered statements."""
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            return f"Statement Cluster {timezone.now().strftime('%Y%m%d')} - {cluster_id}"
        
        try:
            llm = GoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=api_key)
            
            # Use full statements for better context
            statements_text = []
            for stmt in cluster_statements[:5]:  # Use up to 5 statements
                statements_text.append(f"- {stmt.full_statement[:200]}...")
            
            statements_str = "\\n".join(statements_text)
            
            prompt = f"""Analyze the following news statements and identify the main narrative theme. Generate a concise, descriptive name (2-4 words) that captures the core story or topic:

Statements:
{statements_str}

Instructions:
- Create a journalistic, descriptive name
- Keep it concise (2-4 words maximum)  
- Focus on the main theme, event, or topic
- Use title case (e.g., "Climate Policy Debate", "Tech Regulation Update")
- Do not include dates or numbers
- Respond with ONLY the narrative name, nothing else

Narrative name:"""
            
            response = llm.invoke(prompt)
            narrative_name = response.strip().replace('"', '').replace("'", "")
            
            if len(narrative_name.split()) <= 6 and len(narrative_name) <= 50:
                return narrative_name
            else:
                return f"Statement Cluster {timezone.now().strftime('%Y%m%d')} - {cluster_id}"
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"Failed to generate LLM name for cluster {cluster_id}: {str(e)}")
            )
            return f"Statement Cluster {timezone.now().strftime('%Y%m%d')} - {cluster_id}"
    
    def handle(self, *args, **options):
        days_back = options['days']
        n_clusters = options['clusters']
        min_sources = options['min_sources']
        min_statements = options['min_statements']
        coherence_threshold = options['coherence_threshold']
        
        cutoff_date = timezone.now() - timedelta(days=days_back)
        
        # Get statements from recent articles with embeddings
        recent_statements = Statement.objects.filter(
            article__published_date__gte=cutoff_date,
            embedding__isnull=False,
            confidence_score__gte=0.5  # Only use high-confidence statements
        ).select_related('article')
        
        if recent_statements.count() < n_clusters:
            self.stdout.write(
                self.style.ERROR(f"Not enough statements with embeddings found. Found: {recent_statements.count()}, need at least: {n_clusters}")
            )
            return
        
        self.stdout.write(f"Found {recent_statements.count()} statements to cluster")
        
        # Extract embeddings
        embeddings = []
        statements = list(recent_statements)
        
        for statement in statements:
            if statement.embedding is not None:
                embeddings.append(statement.embedding)
        
        embeddings_array = np.array(embeddings)
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings_array)
        
        # Calculate overall silhouette score
        if len(embeddings_array) > n_clusters:
            silhouette_avg = silhouette_score(embeddings_array, cluster_labels)
            self.stdout.write(f"Average silhouette score: {silhouette_avg:.3f}")
        
        narratives_created = 0
        
        # Process each cluster
        for cluster_id in range(n_clusters):
            cluster_indices = np.where(cluster_labels == cluster_id)[0]
            cluster_statements = [statements[i] for i in cluster_indices]
            
            if len(cluster_statements) < min_statements:
                self.stdout.write(f"Cluster {cluster_id}: Too few statements ({len(cluster_statements)} < {min_statements})")
                continue
            
            # Check source diversity
            unique_sources = set(stmt.article.source for stmt in cluster_statements)
            if len(unique_sources) < min_sources:
                self.stdout.write(f"Cluster {cluster_id}: Not enough unique sources ({len(unique_sources)} < {min_sources})")
                continue
            
            # Check date diversity (at least 2 different dates)
            unique_dates = set(stmt.article.published_date.date() for stmt in cluster_statements)
            if len(unique_dates) < 2:
                self.stdout.write(f"Cluster {cluster_id}: Not enough temporal spread ({len(unique_dates)} days)")
                continue
            
            # Calculate quality metrics
            cluster_embeddings = [embeddings[i] for i in cluster_indices]
            coherence_score = self.calculate_coherence_score(cluster_embeddings)
            
            if coherence_score < coherence_threshold:
                self.stdout.write(f"Cluster {cluster_id}: Low coherence score ({coherence_score:.3f} < {coherence_threshold})")
                continue
            
            source_diversity = self.calculate_source_diversity(cluster_statements)
            near_duplicate_rate = self.calculate_near_duplicate_rate(cluster_statements)
            
            # Generate narrative name
            narrative_name = self.generate_narrative_name(cluster_statements, cluster_id)
            
            # Create description
            sample_statements = [stmt.full_statement[:100] for stmt in cluster_statements[:3]]
            description = f"Narrative with {len(cluster_statements)} statements from {len(unique_sources)} sources. Sample statements: {' | '.join(sample_statements)}"
            
            # Create or update narrative
            narrative, created = Narrative.objects.get_or_create(
                name=narrative_name,
                defaults={
                    'description': description,
                    'source_diversity_score': source_diversity,
                    'support_count': len(cluster_statements),
                    'unique_sources_count': len(unique_sources),
                    'coherence_score': coherence_score,
                    'near_duplicate_rate': near_duplicate_rate,
                    'persistence_days': len(unique_dates)
                }
            )
            
            if not created:
                # Update metrics for existing narrative
                narrative.source_diversity_score = source_diversity
                narrative.support_count = len(cluster_statements)
                narrative.unique_sources_count = len(unique_sources)
                narrative.coherence_score = coherence_score
                narrative.near_duplicate_rate = near_duplicate_rate
                narrative.persistence_days = len(unique_dates)
                narrative.save()
            
            # Create narrative cluster
            cluster = NarrativeCluster.objects.create(
                narrative=narrative,
                cluster_date=timezone.now().date(),
                centroid=kmeans.cluster_centers_[cluster_id].tolist()
            )
            
            # Add statements and articles to cluster
            cluster.statements.add(*cluster_statements)
            articles = list(set(stmt.article for stmt in cluster_statements))
            cluster.articles.add(*articles)
            
            # Create timeline event
            TimelineEvent.objects.create(
                narrative=narrative,
                event_type='emergence',
                description=f"Narrative detected with {len(cluster_statements)} statements (coherence: {coherence_score:.3f}, diversity: {source_diversity:.3f})",
                event_date=timezone.now(),
                significance_score=coherence_score * source_diversity,
                related_articles=articles[:5]  # Add first 5 articles
            )
            
            narratives_created += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created narrative '{narrative_name}': {len(cluster_statements)} statements, "
                    f"{len(unique_sources)} sources, coherence: {coherence_score:.3f}, "
                    f"diversity: {source_diversity:.3f}, duplicates: {near_duplicate_rate:.3f}"
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(f"\\nCompleted! Created {narratives_created} high-quality narratives from statement clustering")
        )