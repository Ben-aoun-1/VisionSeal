#!/usr/bin/env python3
"""
Automated scheduler for VisionSeal scrapers
"""
import asyncio
import schedule
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import subprocess

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

class VisionSealScheduler:
    """Automated scheduler for running scrapers at regular intervals"""
    
    def __init__(self):
        self.running = False
        self.last_ungm_run = None
        self.last_tunipages_run = None
        self.stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'opportunities_found': 0
        }
    
    async def run_ungm_scraper(self):
        """Run UNGM multi-search scraper"""
        print(f"\n🎯 SCHEDULED UNGM SCRAPER RUN")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 45)
        
        try:
            # Import and run UNGM scraper
            sys.path.insert(0, str(Path(__file__).parent.parent))
            
            from multi_search_extractor import multi_search_extraction
            
            opportunities = await multi_search_extraction()
            
            self.last_ungm_run = datetime.now()
            self.stats['total_runs'] += 1
            self.stats['opportunities_found'] += len(opportunities)
            
            if opportunities:
                self.stats['successful_runs'] += 1
                print(f"✅ UNGM scraper completed: {len(opportunities)} opportunities")
            else:
                print("⚠️ UNGM scraper completed with 0 opportunities")
            
            return len(opportunities)
            
        except Exception as e:
            print(f"❌ UNGM scraper failed: {str(e)}")
            self.stats['failed_runs'] += 1
            return 0
    
    async def run_tunipages_scraper(self):
        """Run TuniPages scraper"""
        print(f"\n🎯 SCHEDULED TUNIPAGES SCRAPER RUN")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 45)
        
        try:
            # Import and run TuniPages scraper
            sys.path.insert(0, str(Path(__file__).parent.parent))
            
            from tunipages_improved_scraper import scrape_improved_tunipages
            
            opportunities = await scrape_improved_tunipages()
            
            self.last_tunipages_run = datetime.now()
            self.stats['total_runs'] += 1
            self.stats['opportunities_found'] += len(opportunities)
            
            if opportunities:
                self.stats['successful_runs'] += 1
                print(f"✅ TuniPages scraper completed: {len(opportunities)} opportunities")
            else:
                print("⚠️ TuniPages scraper completed with 0 opportunities")
            
            return len(opportunities)
            
        except Exception as e:
            print(f"❌ TuniPages scraper failed: {str(e)}")
            self.stats['failed_runs'] += 1
            return 0
    
    async def run_full_scraping_cycle(self):
        """Run both scrapers in sequence"""
        print(f"\n🚀 FULL SCRAPING CYCLE STARTED")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        total_opportunities = 0
        
        # Run UNGM scraper
        ungm_count = await self.run_ungm_scraper()
        total_opportunities += ungm_count
        
        # Wait between scrapers
        await asyncio.sleep(30)
        
        # Run TuniPages scraper
        tunipages_count = await self.run_tunipages_scraper()
        total_opportunities += tunipages_count
        
        print(f"\n📊 CYCLE COMPLETE:")
        print(f"   UNGM: {ungm_count} opportunities")
        print(f"   TuniPages: {tunipages_count} opportunities")
        print(f"   Total: {total_opportunities} opportunities")
        print(f"   Duration: {datetime.now().strftime('%H:%M:%S')}")
        
        await self.cleanup_old_opportunities()
        
        return total_opportunities
    
    async def cleanup_old_opportunities(self):
        """Remove opportunities older than 1 year"""
        try:
            from core.database.supabase_client import supabase_manager
            
            # Calculate cutoff date (1 year ago)
            cutoff_date = datetime.now() - timedelta(days=365)
            
            print(f"\n🧹 Cleaning up opportunities older than {cutoff_date.strftime('%Y-%m-%d')}")
            
            # This would be implemented in supabase_manager if needed
            # For now, we'll just log the intent
            print("✅ Cleanup completed (placeholder)")
            
        except Exception as e:
            print(f"⚠️ Cleanup failed: {str(e)}")
    
    def setup_schedule(self):
        """Setup automated schedule"""
        print("⏰ SETTING UP AUTOMATED SCHEDULE")
        print("=" * 35)
        
        # Schedule UNGM scraper every 6 hours
        schedule.every(6).hours.do(self.schedule_ungm_job)
        print("✅ UNGM scraper: Every 6 hours")
        
        # Schedule TuniPages scraper every 12 hours  
        schedule.every(12).hours.do(self.schedule_tunipages_job)
        print("✅ TuniPages scraper: Every 12 hours")
        
        # Schedule full cycle once daily at 6 AM
        schedule.every().day.at("06:00").do(self.schedule_full_cycle)
        print("✅ Full cycle: Daily at 6:00 AM")
        
        print()
        print("📅 Next scheduled runs:")
        for job in schedule.jobs:
            print(f"   {job}")
    
    def schedule_ungm_job(self):
        """Wrapper to run UNGM scraper in event loop"""
        asyncio.run(self.run_ungm_scraper())
    
    def schedule_tunipages_job(self):
        """Wrapper to run TuniPages scraper in event loop"""
        asyncio.run(self.run_tunipages_scraper())
    
    def schedule_full_cycle(self):
        """Wrapper to run full cycle in event loop"""
        asyncio.run(self.run_full_scraping_cycle())
    
    def print_stats(self):
        """Print current statistics"""
        print(f"\n📊 SCHEDULER STATISTICS:")
        print(f"   Total runs: {self.stats['total_runs']}")
        print(f"   Successful: {self.stats['successful_runs']}")
        print(f"   Failed: {self.stats['failed_runs']}")
        print(f"   Opportunities found: {self.stats['opportunities_found']}")
        print(f"   Last UNGM run: {self.last_ungm_run or 'Never'}")
        print(f"   Last TuniPages run: {self.last_tunipages_run or 'Never'}")
    
    def run_scheduler(self):
        """Run the scheduler indefinitely"""
        print("🎯 VISIONSEAL AUTOMATED SCHEDULER")
        print("=" * 40)
        print("🚀 Starting automated African tender discovery")
        print("✅ UNGM and TuniPages scrapers")
        print("✅ Automatic data collection and storage")
        print("✅ Scheduled runs for continuous updates")
        print()
        
        self.setup_schedule()
        self.running = True
        
        print("🔄 Scheduler is running...")
        print("Press Ctrl+C to stop")
        print("-" * 50)
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
                # Print stats every hour
                if datetime.now().minute == 0:
                    self.print_stats()
                    
        except KeyboardInterrupt:
            print("\n🛑 Scheduler stopped by user")
            self.running = False
        except Exception as e:
            print(f"\n❌ Scheduler error: {str(e)}")
            self.running = False
        
        print("✅ Scheduler shutdown complete")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VisionSeal Automated Scheduler")
    parser.add_argument("--run-now", action="store_true", help="Run scrapers immediately")
    parser.add_argument("--ungm-only", action="store_true", help="Run only UNGM scraper")
    parser.add_argument("--tunipages-only", action="store_true", help="Run only TuniPages scraper")
    parser.add_argument("--schedule", action="store_true", help="Start automated scheduler")
    
    args = parser.parse_args()
    
    scheduler = VisionSealScheduler()
    
    if args.run_now:
        if args.ungm_only:
            asyncio.run(scheduler.run_ungm_scraper())
        elif args.tunipages_only:
            asyncio.run(scheduler.run_tunipages_scraper())
        else:
            asyncio.run(scheduler.run_full_scraping_cycle())
    elif args.schedule:
        scheduler.run_scheduler()
    else:
        print("🎯 VisionSeal Automated Scheduler")
        print()
        print("Usage options:")
        print("  --run-now           Run scrapers immediately")
        print("  --ungm-only         Run only UNGM scraper")
        print("  --tunipages-only    Run only TuniPages scraper")
        print("  --schedule          Start automated scheduler")
        print()
        print("Examples:")
        print("  python automated_scraper.py --run-now")
        print("  python automated_scraper.py --schedule")
        print("  python automated_scraper.py --ungm-only --run-now")

if __name__ == "__main__":
    main()