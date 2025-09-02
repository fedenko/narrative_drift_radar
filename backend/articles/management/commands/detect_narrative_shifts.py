from django.core.management.base import BaseCommand
from django.utils import timezone
from sklearn.cluster import KMeans
import numpy as np
from datetime import datetime, timedelta
from articles.models import Article, Narrative, NarrativeCluster, TimelineEvent


class Command(BaseCommand):
    help = 'Detect narrative shifts using clustering'
    
    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
        parser.add_argument('--clusters', type=int, default=5, help='Number of clusters')
    
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
            if article.embedding:
                embeddings.append(article.embedding)
        
        if len(embeddings) < n_clusters:
            self.stdout.write(
                self.style.WARNING('Not enough valid embeddings for clustering')
            )
            return
        
        embeddings_array = np.array(embeddings)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings_array)
        
        clusters_created = 0
        
        for cluster_id in range(n_clusters):
            cluster_articles = [articles[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
            
            if not cluster_articles:
                continue
            
            narrative_name = f"Narrative Cluster {timezone.now().strftime('%Y%m%d')} - {cluster_id}"
            
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