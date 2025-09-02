from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Narrative, NarrativeCluster, TimelineEvent
from .serializers import NarrativeSerializer, NarrativeClusterSerializer, TimelineEventSerializer


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
