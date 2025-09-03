from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from sklearn.cluster import KMeans
import numpy as np
from datetime import datetime, timedelta
from langchain_google_genai import GoogleGenerativeAI
from articles.models import Article
from narratives.models import Narrative, NarrativeCluster, TimelineEvent


class Command(BaseCommand):
    help = 'Detect narrative shifts using clustering'
    
    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
        parser.add_argument('--clusters', type=int, default=5, help='Number of clusters')
    
    def generate_narrative_name(self, cluster_articles, cluster_id):
        """Generate a meaningful narrative name using LLM based on cluster articles."""
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            return f"Narrative Cluster {timezone.now().strftime('%Y%m%d')} - {cluster_id}"
        
        try:
            # Initialize LLM
            llm = GoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=api_key)
            
            # Prepare article titles for analysis
            titles = [article.title for article in cluster_articles[:5]]  # Use up to 5 titles
            titles_text = "\n".join([f"- {title}" for title in titles])
            
            # Create prompt for generating narrative name
            prompt = f"""Analyze the following news article titles and identify the main narrative theme. Generate a concise, descriptive name (2-4 words) that captures the core story or topic:

Article titles:
{titles_text}

Instructions:
- Create a journalistic, descriptive name
- Keep it concise (2-4 words maximum)
- Focus on the main theme, event, or topic
- Use title case (e.g., "Climate Policy Debate", "Tech Regulation Update")
- Do not include dates or numbers
- Respond with ONLY the narrative name, nothing else

Narrative name:"""
            
            # Generate the name
            response = llm.invoke(prompt)
            narrative_name = response.strip().replace('"', '').replace("'", "")
            
            # Validate the response (basic checks)
            if len(narrative_name.split()) <= 6 and len(narrative_name) <= 50:
                return narrative_name
            else:
                # Fallback if response is too long
                return f"Narrative Cluster {timezone.now().strftime('%Y%m%d')} - {cluster_id}"
                
        except Exception as e:
            # Fallback to original naming if LLM fails
            self.stdout.write(
                self.style.WARNING(f"Failed to generate LLM name for cluster {cluster_id}: {str(e)}")
            )
            return f"Narrative Cluster {timezone.now().strftime('%Y%m%d')} - {cluster_id}"
    
    def handle(self, *args, **options):
        days_back = options['days']
        n_clusters = options['clusters']
        
        cutoff_date = timezone.now() - timedelta(days=days_back)
        recent_articles = Article.objects.filter(
            published_date__gte=cutoff_date,
            embedding__isnull=False
        )
        
        if recent_articles.count() < n_clusters:
            self.stdout.write(
                self.style.WARNING('Not enough articles with embeddings for clustering')
            )
            return
        
        embeddings = []
        articles = list(recent_articles)
        
        for article in articles:
            if article.embedding is not None:
                embeddings.append(article.embedding)
        
        if len(embeddings) < n_clusters:
            self.stdout.write(
                self.style.WARNING('Not enough valid embeddings for clustering')
            )
            return
        
        embeddings_array = np.array(embeddings)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings_array)
        
        clusters_created = 0
        
        for cluster_id in range(n_clusters):
            cluster_articles = [articles[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
            
            if not cluster_articles:
                continue
            
            # Generate meaningful narrative name using LLM
            narrative_name = self.generate_narrative_name(cluster_articles, cluster_id)
            
            sample_titles = [article.title for article in cluster_articles[:3]]
            description = f"Cluster containing {len(cluster_articles)} articles. Sample: {', '.join(sample_titles)}"
            
            narrative, created = Narrative.objects.get_or_create(
                name=narrative_name,
                defaults={'description': description}
            )
            
            cluster, cluster_created = NarrativeCluster.objects.get_or_create(
                narrative=narrative,
                cluster_date=timezone.now().date(),
                defaults={'centroid': kmeans.cluster_centers_[cluster_id].tolist()}
            )
            
            if cluster_created:
                cluster.articles.set(cluster_articles)
                clusters_created += 1
                
                if len(cluster_articles) > 5:
                    TimelineEvent.objects.create(
                        narrative=narrative,
                        event_type='emergence',
                        description=f"New narrative cluster emerged with {len(cluster_articles)} articles",
                        event_date=timezone.now(),
                        significance_score=len(cluster_articles) / 10.0
                    )
                
                self.stdout.write(f"Created cluster: {narrative_name}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {clusters_created} narrative clusters')
        )