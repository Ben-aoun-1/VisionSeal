#!/usr/bin/env python3
"""
CLI for VisionSeal Automation Management
Provides command-line interface for task management and monitoring
"""
import asyncio
import sys
import argparse
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

from automation.task_manager import automation_manager, TaskPriority
from core.logging.setup import get_logger
from core.config.settings import settings

logger = get_logger("automation_cli")


class AutomationCLI:
    """Command-line interface for automation management"""
    
    def __init__(self):
        self.automation_manager = automation_manager
    
    def start_session(self, source: str, config: Optional[Dict[str, Any]] = None) -> str:
        """Start a scraping session"""
        try:
            task_id = self.automation_manager.schedule_scraping_session(
                source=source,
                config=config,
                priority=TaskPriority.HIGH
            )
            
            if task_id:
                print(f"✅ Started {source} scraping session: {task_id}")
                return task_id
            else:
                print(f"❌ Failed to start {source} scraping session")
                return None
                
        except Exception as e:
            print(f"❌ Error starting {source} session: {str(e)}")
            return None
    
    def start_all_sessions(self, config: Optional[Dict[str, Any]] = None) -> List[str]:
        """Start all available scraping sessions"""
        try:
            task_ids = self.automation_manager.schedule_all_scrapers(config)
            
            print(f"✅ Started {len(task_ids)} scraping sessions:")
            for task_id in task_ids:
                session_info = self.automation_manager.get_session_status(task_id)
                source = session_info.get('task_info', {}).metadata.get('source', 'unknown')
                print(f"  - {source}: {task_id}")
            
            return task_ids
            
        except Exception as e:
            print(f"❌ Error starting all sessions: {str(e)}")
            return []
    
    def get_session_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a specific session"""
        try:
            session_info = self.automation_manager.get_session_status(task_id)
            
            if not session_info['status']:
                print(f"❌ Session {task_id} not found")
                return {}
            
            task_info = session_info['task_info']
            result = session_info['result']
            
            status_data = {
                'task_id': task_id,
                'name': task_info.name,
                'status': session_info['status'],
                'source': task_info.metadata.get('source'),
                'created_at': task_info.created_at.isoformat(),
                'last_attempt': task_info.last_attempt.isoformat() if task_info.last_attempt else None,
                'retry_count': task_info.retry_count
            }
            
            if result:
                status_data.update({
                    'execution_time': result.execution_time,
                    'started_at': result.started_at.isoformat() if result.started_at else None,
                    'completed_at': result.completed_at.isoformat() if result.completed_at else None,
                    'error': result.error
                })
                
                if result.result:
                    status_data.update({
                        'tenders_found': result.result.get('tenders_found', 0),
                        'tenders_processed': result.result.get('tenders_processed', 0),
                        'pages_processed': result.result.get('pages_processed', 0)
                    })
            
            return status_data
            
        except Exception as e:
            print(f"❌ Error getting session status: {str(e)}")
            return {}
    
    def list_all_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions"""
        try:
            sessions = self.automation_manager.get_all_sessions()
            
            if not sessions:
                print("📝 No active sessions found")
                return []
            
            session_data = []
            for session in sessions:
                detailed_info = self.get_session_status(session['task_id'])
                session_data.append(detailed_info)
            
            return session_data
            
        except Exception as e:
            print(f"❌ Error listing sessions: {str(e)}")
            return []
    
    def cancel_session(self, task_id: str) -> bool:
        """Cancel a session"""
        try:
            success = self.automation_manager.cancel_session(task_id)
            
            if success:
                print(f"✅ Cancelled session {task_id}")
                return True
            else:
                print(f"❌ Could not cancel session {task_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error cancelling session: {str(e)}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get automation metrics"""
        try:
            metrics = self.automation_manager.get_metrics()
            return metrics
            
        except Exception as e:
            print(f"❌ Error getting metrics: {str(e)}")
            return {}
    
    def monitor_session(self, task_id: str, interval: int = 30):
        """Monitor a session until completion"""
        print(f"🔍 Monitoring session {task_id} (checking every {interval}s)")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                status_data = self.get_session_status(task_id)
                
                if not status_data:
                    print(f"❌ Session {task_id} not found")
                    break
                
                status = status_data['status']
                source = status_data.get('source', 'unknown')
                
                print(f"\n📊 Status Update - {datetime.now().strftime('%H:%M:%S')}")
                print(f"   Source: {source}")
                print(f"   Status: {status}")
                print(f"   Retry Count: {status_data['retry_count']}")
                
                if status_data.get('tenders_found') is not None:
                    print(f"   Tenders Found: {status_data['tenders_found']}")
                    print(f"   Tenders Processed: {status_data['tenders_processed']}")
                    print(f"   Pages Processed: {status_data['pages_processed']}")
                
                if status in ['completed', 'failed', 'cancelled']:
                    print(f"\n🏁 Session {task_id} finished with status: {status}")
                    if status_data.get('execution_time'):
                        print(f"   Execution Time: {status_data['execution_time']:.2f}s")
                    if status_data.get('error'):
                        print(f"   Error: {status_data['error']}")
                    break
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n⏹️  Stopped monitoring session {task_id}")
    
    def print_status_table(self, sessions: List[Dict[str, Any]]):
        """Print sessions in a formatted table"""
        if not sessions:
            print("📝 No sessions to display")
            return
        
        # Calculate column widths
        widths = {
            'task_id': max(len(s.get('task_id', '')[:12]) for s in sessions) + 2,
            'source': max(len(s.get('source', '')) for s in sessions) + 2,
            'status': max(len(s.get('status', '')) for s in sessions) + 2,
            'tenders': 8,
            'pages': 6,
            'created': 12
        }
        
        # Header
        header = (
            f"{'Task ID':<{widths['task_id']}}"
            f"{'Source':<{widths['source']}}"
            f"{'Status':<{widths['status']}}"
            f"{'Tenders':<{widths['tenders']}}"
            f"{'Pages':<{widths['pages']}}"
            f"{'Created':<{widths['created']}}"
        )
        
        print("\n" + "=" * len(header))
        print(header)
        print("=" * len(header))
        
        # Rows
        for session in sessions:
            task_id = session.get('task_id', '')[:12]
            source = session.get('source', 'unknown')
            status = session.get('status', 'unknown')
            tenders = f"{session.get('tenders_found', 0)}/{session.get('tenders_processed', 0)}"
            pages = str(session.get('pages_processed', 0))
            created = session.get('created_at', '')[:10] if session.get('created_at') else 'unknown'
            
            # Status emoji
            status_emoji = {
                'pending': '⏳',
                'running': '🔄',
                'completed': '✅',
                'failed': '❌',
                'cancelled': '⏹️',
                'retrying': '🔁'
            }.get(status, '❓')
            
            row = (
                f"{task_id:<{widths['task_id']}}"
                f"{source:<{widths['source']}}"
                f"{status_emoji} {status:<{widths['status']-2}}"
                f"{tenders:<{widths['tenders']}}"
                f"{pages:<{widths['pages']}}"
                f"{created:<{widths['created']}}"
            )
            
            print(row)
        
        print("=" * len(header))
        print(f"Total sessions: {len(sessions)}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="VisionSeal Automation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start a scraping session')
    start_parser.add_argument('source', choices=['ungm', 'tunipages', 'all'], help='Scraper source')
    start_parser.add_argument('--max-pages', type=int, default=5, help='Maximum pages to scrape')
    start_parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get session status')
    status_parser.add_argument('task_id', help='Task ID to check')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all sessions')
    list_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Cancel command
    cancel_parser = subparsers.add_parser('cancel', help='Cancel a session')
    cancel_parser.add_argument('task_id', help='Task ID to cancel')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor a session')
    monitor_parser.add_argument('task_id', help='Task ID to monitor')
    monitor_parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')
    
    # Metrics command
    metrics_parser = subparsers.add_parser('metrics', help='Show automation metrics')
    metrics_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = AutomationCLI()
    
    try:
        if args.command == 'start':
            config = {
                'max_pages': args.max_pages,
                'headless': args.headless
            }
            
            if args.source == 'all':
                cli.start_all_sessions(config)
            else:
                cli.start_session(args.source, config)
        
        elif args.command == 'status':
            status_data = cli.get_session_status(args.task_id)
            if status_data:
                print(f"\n📊 Session Status: {args.task_id}")
                print(f"   Source: {status_data.get('source', 'unknown')}")
                print(f"   Status: {status_data['status']}")
                print(f"   Created: {status_data.get('created_at', 'unknown')}")
                print(f"   Retry Count: {status_data['retry_count']}")
                
                if status_data.get('tenders_found') is not None:
                    print(f"   Tenders Found: {status_data['tenders_found']}")
                    print(f"   Tenders Processed: {status_data['tenders_processed']}")
                    print(f"   Pages Processed: {status_data['pages_processed']}")
                
                if status_data.get('execution_time'):
                    print(f"   Execution Time: {status_data['execution_time']:.2f}s")
                
                if status_data.get('error'):
                    print(f"   Error: {status_data['error']}")
        
        elif args.command == 'list':
            sessions = cli.list_all_sessions()
            
            if args.json:
                print(json.dumps(sessions, indent=2, default=str))
            else:
                cli.print_status_table(sessions)
        
        elif args.command == 'cancel':
            cli.cancel_session(args.task_id)
        
        elif args.command == 'monitor':
            cli.monitor_session(args.task_id, args.interval)
        
        elif args.command == 'metrics':
            metrics = cli.get_metrics()
            
            if args.json:
                print(json.dumps(metrics, indent=2))
            else:
                print("\n📈 Automation Metrics")
                print(f"   Tasks Created: {metrics.get('tasks_created', 0)}")
                print(f"   Tasks Completed: {metrics.get('tasks_completed', 0)}")
                print(f"   Tasks Failed: {metrics.get('tasks_failed', 0)}")
                print(f"   Tasks Retried: {metrics.get('tasks_retried', 0)}")
                print(f"   Active Tasks: {metrics.get('active_tasks', 0)}")
                print(f"   Pending Tasks: {metrics.get('pending_tasks', 0)}")
                print(f"   Average Execution Time: {metrics.get('average_execution_time', 0):.2f}s")
                
                # Calculate success rate
                total = metrics.get('tasks_created', 0)
                success_rate = (metrics.get('tasks_completed', 0) / max(total, 1)) * 100
                print(f"   Success Rate: {success_rate:.1f}%")
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()