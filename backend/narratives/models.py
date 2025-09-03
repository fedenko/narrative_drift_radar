from django.db import models
from pgvector.django import VectorField


class Statement(models.Model):
    """
    Represents extracted statements from articles in format: who → what → why → consequence
    """
    article = models.ForeignKey('articles.Article', on_delete=models.CASCADE, related_name='statements')
    
    # Extracted components
    actor = models.CharField(max_length=300, help_text="Who is making the statement or performing the action")
    action = models.TextField(help_text="What is being said or done")
    reason = models.TextField(blank=True, help_text="Why - the reasoning or cause")
    consequence = models.TextField(blank=True, help_text="Expected or stated outcome/consequence")
    
    # Full extracted statement
    full_statement = models.TextField(help_text="Complete extracted statement text")
    
    # Vector embedding for clustering
    embedding = VectorField(dimensions=768, null=True, blank=True)
    
    # Metadata
    confidence_score = models.FloatField(default=0.0, help_text="LLM confidence in extraction (0-1)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.actor}: {self.action[:50]}..."


class Narrative(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Quality metrics for narrative validation
    source_diversity_score = models.FloatField(default=0.0, help_text="Entropy-based diversity of sources")
    support_count = models.IntegerField(default=0, help_text="Number of supporting statements/articles")
    unique_sources_count = models.IntegerField(default=0, help_text="Number of unique domains")
    coherence_score = models.FloatField(default=0.0, help_text="Average cosine similarity within cluster")
    near_duplicate_rate = models.FloatField(default=0.0, help_text="Rate of near-duplicate content")
    persistence_days = models.IntegerField(default=0, help_text="Number of days narrative persisted")
    
    def __str__(self):
        return self.name


class NarrativeCluster(models.Model):
    narrative = models.ForeignKey(Narrative, on_delete=models.CASCADE)
    articles = models.ManyToManyField('articles.Article')
    statements = models.ManyToManyField(Statement, blank=True, help_text="Clustered statements that form this narrative")
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
