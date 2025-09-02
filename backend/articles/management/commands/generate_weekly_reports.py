from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
import google.generativeai as genai
from datetime import datetime, timedelta
from articles.models import Article
from narratives.models import Narrative, TimelineEvent


class Command(BaseCommand):
    help = 'Generate weekly narrative analysis reports'
    
    def handle(self, *args, **options):
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            self.stdout.write(
                self.style.ERROR('GOOGLE_API_KEY not configured in settings')
            )
            return
        
        genai.configure(api_key=api_key)
        
        week_ago = timezone.now() - timedelta(days=7)
        
        recent_events = TimelineEvent.objects.filter(event_date__gte=week_ago)
        active_narratives = Narrative.objects.filter(is_active=True)
        recent_articles = Article.objects.filter(published_date__gte=week_ago)
        
        if not recent_events.exists() and not recent_articles.exists():
            self.stdout.write(self.style.WARNING('No recent activity to analyze'))
            return
        
        context = []
        
        if recent_events.exists():
            context.append("Recent Timeline Events:")
            for event in recent_events[:10]:
                context.append(f"- {event.narrative.name}: {event.event_type} - {event.description}")
        
        if active_narratives.exists():
            context.append("\nActive Narratives:")
            for narrative in active_narratives[:5]:
                context.append(f"- {narrative.name}: {narrative.description}")
        
        context.append(f"\nTotal articles processed this week: {recent_articles.count()}")
        
        prompt = f"""
        Analyze the following narrative drift data from the past week and provide insights:

        {chr(10).join(context)}

        Please provide:
        1. Key narrative trends and shifts
        2. Emerging themes or topics
        3. Significant changes in information landscape
        4. Recommendations for monitoring

        Keep the analysis concise and actionable.
        """
        
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            
            report_content = response.text
            
            self.stdout.write(self.style.SUCCESS('Weekly Report Generated:'))
            self.stdout.write('=' * 50)
            self.stdout.write(report_content)
            self.stdout.write('=' * 50)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to generate report: {str(e)}')
            )