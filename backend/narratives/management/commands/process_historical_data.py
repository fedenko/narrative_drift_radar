from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.db.models import Count, Q
from datetime import datetime, timedelta
import numpy as np
from articles.models import Article
from narratives.models import Narrative, TimelineEvent
from narratives.management.commands.cost_efficient_clustering import Command as ClusteringCommand
from narratives.utils.content_compression import ContentCompressor


class Command(BaseCommand):
    help = 'Process historical data for the past 2 months with cost optimization'
    
    def add_arguments(self, parser):
        parser.add_argument('--months', type=int, default=2, help='Number of months back to process')
        parser.add_argument('--clusters-per-week', type=int, default=6, help='Clusters per week (reduced for historical)')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without running')
        parser.add_argument('--skip-existing', action='store_true', help='Skip weeks that already have narratives')
        parser.add_argument('--min-sources', type=int, default=3, help='Minimum sources per narrative')
        parser.add_argument('--coherence-threshold', type=float, default=0.5, help='Minimum coherence threshold')
    
    def __init__(self):
        super().__init__()
        self.clustering_command = None
    
    def get_week_boundaries(self, months_back: int):
        """Generate list of week boundaries for processing."""
        end_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=30 * months_back)
        
        weeks = []
        current_date = start_date
        
        while current_date < end_date:
            week_end = min(current_date + timedelta(days=7), end_date)
            weeks.append((current_date, week_end))
            current_date = week_end
        
        return weeks
    
    def check_week_processed(self, start_date: datetime, end_date: datetime) -> bool:
        """Check if week has already been processed."""
        existing_events = TimelineEvent.objects.filter(
            event_date__gte=start_date,
            event_date__lt=end_date
        ).count()
        
        return existing_events > 0
    
    def get_week_article_stats(self, start_date: datetime, end_date: datetime) -> dict:
        """Get statistics for articles in date range."""
        articles = Article.objects.filter(
            published_date__gte=start_date,
            published_date__lt=end_date
        )
        
        total_articles = articles.count()
        articles_with_embeddings = articles.filter(embedding__isnull=False).count()
        unique_sources = articles.values('source').distinct().count()
        
        return {
            'total_articles': total_articles,
            'articles_with_embeddings': articles_with_embeddings,
            'unique_sources': unique_sources,
            'coverage': articles_with_embeddings / total_articles if total_articles > 0 else 0
        }
    
    def estimate_processing_cost(self, weeks_to_process: list, clusters_per_week: int) -> dict:
        """Estimate processing cost for historical data."""
        total_clusters = len(weeks_to_process) * clusters_per_week
        weekly_briefs = len(weeks_to_process)
        
        # Cost estimates based on optimized pipeline
        cluster_naming_cost = total_clusters * 0.0001  # gemini-1.5-flash
        weekly_brief_cost = weekly_briefs * 0.001     # gemini-2.5-flash
        total_estimated_cost = cluster_naming_cost + weekly_brief_cost
        
        return {
            'weeks': len(weeks_to_process),
            'estimated_clusters': total_clusters,
            'cluster_naming_calls': total_clusters,
            'weekly_brief_calls': weekly_briefs,
            'estimated_cost_usd': total_estimated_cost,
            'cost_breakdown': {
                'cluster_naming': cluster_naming_cost,
                'weekly_briefs': weekly_brief_cost
            }
        }
    
    def process_historical_batch(self, weeks_to_process: list, options: dict) -> dict:
        """Process historical weeks using the clustering command."""
        
        # Initialize clustering command with Ukrainian support
        self.clustering_command = ClusteringCommand()
        # Ensure Ukrainian language support is initialized
        self.clustering_command.compressor = ContentCompressor(language='uk')
        
        results = {
            'weeks_processed': 0,
            'narratives_created': 0,
            'total_llm_calls': 0,
            'total_cost': 0.0,
            'weeks_skipped': 0
        }
        
        for i, (start_date, end_date) in enumerate(weeks_to_process, 1):
            week_str = f"Week {i}/{len(weeks_to_process)}: {start_date.date()} - {end_date.date()}"
            
            # Check if already processed
            if options['skip_existing'] and self.check_week_processed(start_date, end_date):
                self.stdout.write(f"⏭️  {week_str} - Already processed, skipping")
                results['weeks_skipped'] += 1
                continue
            
            # Get week stats
            stats = self.get_week_article_stats(start_date, end_date)
            
            # Skip if insufficient data
            if stats['articles_with_embeddings'] < options['clusters_per_week']:
                self.stdout.write(
                    f"⚠️  {week_str} - Insufficient articles ({stats['articles_with_embeddings']}), skipping"
                )
                results['weeks_skipped'] += 1
                continue
            
            self.stdout.write(
                f"🔄 {week_str} - {stats['articles_with_embeddings']} articles, "
                f"{stats['unique_sources']} sources"
            )
            
            # Process using clustering command
            try:
                week_narratives = self.clustering_command.process_week_batch(
                    start_date, end_date,
                    options['clusters_per_week'],
                    options['min_sources'],
                    5,  # min_articles
                    options['coherence_threshold']
                )
                
                # Generate weekly brief
                if week_narratives:
                    brief = self.clustering_command.generate_weekly_brief(week_narratives)
                    self.stdout.write(f"   📋 Brief: {brief[:100]}...")
                
                results['weeks_processed'] += 1
                results['narratives_created'] += len(week_narratives)
                results['total_llm_calls'] += self.clustering_command.llm_calls
                results['total_cost'] += self.clustering_command.total_cost
                
                # Reset counters for next week
                self.clustering_command.llm_calls = 0
                self.clustering_command.total_cost = 0.0
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ {week_str} - Processing failed: {str(e)}")
                )
        
        return results
    
    def handle(self, *args, **options):
        months = options['months']
        clusters_per_week = options['clusters_per_week']
        dry_run = options['dry_run']
        skip_existing = options['skip_existing']
        
        self.stdout.write(
            self.style.SUCCESS(f"📅 Historical Data Processing: Past {months} months")
        )
        
        # Get week boundaries
        weeks = self.get_week_boundaries(months)
        self.stdout.write(f"Found {len(weeks)} weeks to potentially process")
        
        # Filter weeks that need processing
        weeks_to_process = []
        for start_date, end_date in weeks:
            if skip_existing and self.check_week_processed(start_date, end_date):
                continue
            
            stats = self.get_week_article_stats(start_date, end_date)
            if stats['articles_with_embeddings'] >= clusters_per_week:
                weeks_to_process.append((start_date, end_date))
        
        self.stdout.write(f"Will process {len(weeks_to_process)} weeks")
        
        # Show processing plan
        if weeks_to_process:
            self.stdout.write("\\n📋 Processing Plan:")
            for i, (start_date, end_date) in enumerate(weeks_to_process[:5], 1):
                stats = self.get_week_article_stats(start_date, end_date)
                self.stdout.write(
                    f"  {i}. {start_date.date()} - {end_date.date()}: "
                    f"{stats['articles_with_embeddings']} articles, {stats['unique_sources']} sources"
                )
            if len(weeks_to_process) > 5:
                self.stdout.write(f"  ... and {len(weeks_to_process) - 5} more weeks")
        
        # Cost estimation
        cost_estimate = self.estimate_processing_cost(weeks_to_process, clusters_per_week)
        self.stdout.write("\\n💰 Cost Estimate:")
        self.stdout.write(f"  • Weeks: {cost_estimate['weeks']}")
        self.stdout.write(f"  • Expected clusters: {cost_estimate['estimated_clusters']}")
        self.stdout.write(f"  • LLM calls: {cost_estimate['cluster_naming_calls']} naming + {cost_estimate['weekly_brief_calls']} briefs")
        self.stdout.write(f"  • Estimated cost: ${cost_estimate['estimated_cost_usd']:.3f}")
        
        # Dry run exit
        if dry_run:
            self.stdout.write(self.style.WARNING("\\n🔍 Dry run completed - no processing performed"))
            return
        
        # Confirm processing
        if not options.get('verbosity', 1) == 0:  # Skip confirmation in non-interactive mode
            confirm = input(f"\\nProceed with processing {len(weeks_to_process)} weeks? (y/N): ")
            if confirm.lower() != 'y':
                self.stdout.write("Cancelled.")
                return
        
        # Process historical data
        self.stdout.write("\\n🚀 Starting historical processing...")
        
        results = self.process_historical_batch(weeks_to_process, options)
        
        # Final summary
        self.stdout.write("\\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("📊 Historical Processing Complete!"))
        self.stdout.write(f"✅ Weeks processed: {results['weeks_processed']}")
        self.stdout.write(f"⏭️  Weeks skipped: {results['weeks_skipped']}")
        self.stdout.write(f"📰 Narratives created: {results['narratives_created']}")
        self.stdout.write(f"🤖 LLM calls made: {results['total_llm_calls']}")
        self.stdout.write(f"💵 Total cost: ${results['total_cost']:.3f}")
        
        if results['total_cost'] > 0:
            cost_per_narrative = results['total_cost'] / results['narratives_created']
            self.stdout.write(f"📈 Cost per narrative: ${cost_per_narrative:.4f}")
        
        # Recommendations
        if results['weeks_skipped'] > 0:
            self.stdout.write(f"\\n💡 Tip: {results['weeks_skipped']} weeks were skipped due to insufficient data")
            self.stdout.write("   Consider running article collection for those periods first")
        
        if results['narratives_created'] > 0:
            self.stdout.write("\\n🎯 Next steps:")
            self.stdout.write("   • Review generated narratives in the web interface")
            self.stdout.write("   • Run regular weekly processing going forward")
            self.stdout.write("   • Consider adjusting quality thresholds based on results")