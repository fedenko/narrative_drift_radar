from django.db import models
from pgvector.django import VectorField


class Narrative(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class NarrativeCluster(models.Model):
    narrative = models.ForeignKey(Narrative, on_delete=models.CASCADE)
    articles = models.ManyToManyField('articles.Article')
    created_at = models.DateTimeField(auto_now_add=True)
    cluster_date = models.DateField()
    centroid = VectorField(dimensions=768, null=True, blank=True)
    
    class Meta:
        ordering = ['-cluster_date']


class TimelineEvent(models.Model):
    EVENT_TYPES = [
        ('emergence', 'Narrative Emergence'),
        ('shift', 'Narrative Shift'),
        ('peak', 'Narrative Peak'),
        ('decline', 'Narrative Decline'),
    ]
    
    narrative = models.ForeignKey(Narrative, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    description = models.TextField()
    event_date = models.DateTimeField()
    significance_score = models.FloatField(default=0.0)
    related_articles = models.ManyToManyField('articles.Article', blank=True)
    
    class Meta:
        ordering = ['-event_date']
    
    def __str__(self):
        return f"{self.narrative.name} - {self.get_event_type_display()}"
