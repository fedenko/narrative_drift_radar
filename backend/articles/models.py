from django.db import models
from pgvector.django import VectorField


class Article(models.Model):
    title = models.CharField(max_length=500)
    content = models.TextField()
    url = models.URLField(unique=True)
    published_date = models.DateTimeField()
    source = models.CharField(max_length=200)
    embedding = VectorField(dimensions=768, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-published_date']
    
    def __str__(self):
        return self.title


class Narrative(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class NarrativeCluster(models.Model):
    narrative = models.ForeignKey(Narrative, on_delete=models.CASCADE)
    articles = models.ManyToManyField(Article)
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
    related_articles = models.ManyToManyField(Article, blank=True)
    
    class Meta:
        ordering = ['-event_date']
    
    def __str__(self):
        return f"{self.narrative.name} - {self.get_event_type_display()}"
