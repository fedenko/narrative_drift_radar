from rest_framework import serializers
from .models import Narrative, NarrativeCluster, TimelineEvent
from articles.serializers import ArticleSerializer


class NarrativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Narrative
        fields = ['id', 'name', 'description', 'created_at', 'is_active']


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