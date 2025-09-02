from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django_filters.rest_framework import DjangoFilterBackend
from .models import Article, Narrative, NarrativeCluster, TimelineEvent
from .serializers import ArticleSerializer, NarrativeSerializer, NarrativeClusterSerializer, TimelineEventSerializer


class ArticleListView(generics.ListAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['source', 'published_date']
    search_fields = ['title', 'content']
    ordering_fields = ['published_date', 'created_at']
    ordering = ['-published_date']


class NarrativeListView(generics.ListAPIView):
    queryset = Narrative.objects.filter(is_active=True)
    serializer_class = NarrativeSerializer
    ordering = ['-created_at']


class TimelineView(generics.ListAPIView):
    queryset = TimelineEvent.objects.all()
    serializer_class = TimelineEventSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event_type', 'narrative']
    ordering = ['-event_date']


class NarrativeClusterListView(generics.ListAPIView):
    queryset = NarrativeCluster.objects.all()
    serializer_class = NarrativeClusterSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['narrative', 'cluster_date']
    ordering = ['-cluster_date']


@api_view(['GET'])
def weekly_reports(request):
    return Response({
        'message': 'Weekly reports endpoint - implementation pending',
        'reports': []
    })
