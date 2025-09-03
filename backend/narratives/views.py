from rest_framework import generics, filters
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .models import Narrative, NarrativeCluster, TimelineEvent
from .serializers import NarrativeSerializer, NarrativeClusterSerializer, TimelineEventSerializer


class TimelinePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class NarrativeListView(generics.ListAPIView):
    queryset = Narrative.objects.filter(is_active=True, support_count__gt=0)
    serializer_class = NarrativeSerializer
    ordering = ['-support_count', '-created_at']  # Order by relevance first, then by creation date


class TimelineView(generics.ListAPIView):
    queryset = TimelineEvent.objects.filter(narrative__support_count__gt=0)
    serializer_class = TimelineEventSerializer
    pagination_class = TimelinePagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event_type', 'narrative']
    ordering = ['-significance_score', '-event_date']  # Order by significance first


class NarrativeClusterListView(generics.ListAPIView):
    queryset = NarrativeCluster.objects.all()
    serializer_class = NarrativeClusterSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['narrative', 'cluster_date']
    ordering = ['-cluster_date']
