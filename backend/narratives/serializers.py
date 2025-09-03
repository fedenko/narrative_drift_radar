from rest_framework import serializers
from .models import Narrative, NarrativeCluster, TimelineEvent, Statement
from articles.serializers import ArticleSerializer


class StatementSerializer(serializers.ModelSerializer):
    article_title = serializers.CharField(source='article.title', read_only=True)
    article_source = serializers.CharField(source='article.source', read_only=True)
    
    class Meta:
        model = Statement
        fields = ['id', 'actor', 'action', 'reason', 'consequence', 'full_statement', 
                 'confidence_score', 'article_title', 'article_source', 'created_at']


class NarrativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Narrative
        fields = ['id', 'name', 'description', 'created_at', 'is_active',
                 'source_diversity_score', 'support_count', 'unique_sources_count',
                 'coherence_score', 'near_duplicate_rate', 'persistence_days']


class NarrativeClusterSerializer(serializers.ModelSerializer):
    articles = ArticleSerializer(many=True, read_only=True)
    narrative = NarrativeSerializer(read_only=True)
    
    class Meta:
        model = NarrativeCluster
        fields = ['id', 'narrative', 'articles', 'cluster_date', 'created_at']


class TimelineEventSerializer(serializers.ModelSerializer):
    narrative = NarrativeSerializer(read_only=True)
    related_articles = ArticleSerializer(many=True, read_only=True)
    
    class Meta:
        model = TimelineEvent
        fields = ['id', 'narrative', 'event_type', 'description', 'event_date', 'significance_score', 'related_articles']