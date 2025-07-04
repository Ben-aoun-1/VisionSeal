#!/usr/bin/env python3
"""
Configuration Management CLI for VisionSeal
Provides command-line interface for managing automation configurations
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

from core.config.manager import config_manager, ConfigurationError
from core.logging.setup import get_logger

logger = get_logger("config_cli")


class ConfigCLI:
    """Command-line interface for configuration management"""
    
    def __init__(self):
        self.config_manager = config_manager
    
    def list_profiles(self):
        """List all available profiles"""
        try:
            profiles = self.config_manager.get_all_profiles()
            
            if not profiles:
                print("📝 No profiles found")
                return
            
            print("\n📋 Available Profiles:")
            print("=" * 60)
            
            for name, profile in profiles.items():
                print(f"\n🔹 {name}")
                print(f"   Description: {profile.get('description', 'No description')}")
                
                settings = profile.get('settings', {})
                if settings:
                    print("   Settings:")
                    for key, value in settings.items():
                        print(f"     - {key}: {value}")
                
                created_at = profile.get('created_at')
                if created_at:
                    print(f"   Created: {created_at}")
            
            print("=" * 60)
            print(f"Total profiles: {len(profiles)}")
            
        except Exception as e:
            print(f"❌ Error listing profiles: {str(e)}")
    
    def show_profile(self, name: str):
        """Show detailed profile information"""
        try:
            profile = self.config_manager.get_profile_config(name)
            
            print(f"\n📄 Profile: {name}")
            print("=" * 50)
            print(f"Name: {profile.get('name', name)}")
            print(f"Description: {profile.get('description', 'No description')}")
            
            if profile.get('created_at'):
                print(f"Created: {profile['created_at']}")
            
            settings = profile.get('settings', {})
            if settings:
                print("\nSettings:")
                print(json.dumps(settings, indent=2))
            
        except ConfigurationError as e:
            print(f"❌ {str(e)}")
        except Exception as e:
            print(f"❌ Error showing profile: {str(e)}")
    
    def create_profile(self, name: str, description: str, settings_file: Path = None):
        """Create a new profile"""
        try:
            settings = {}
            
            if settings_file and settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            else:
                # Interactive settings creation
                settings = self._interactive_settings_creation()
            
            self.config_manager.create_profile(name, description, settings)
            print(f"✅ Created profile '{name}' successfully")
            
        except Exception as e:
            print(f"❌ Error creating profile: {str(e)}")
    
    def delete_profile(self, name: str):
        """Delete a profile"""
        try:
            # Confirm deletion
            confirm = input(f"Are you sure you want to delete profile '{name}'? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Profile deletion cancelled")
                return
            
            self.config_manager.delete_profile(name)
            print(f"✅ Deleted profile '{name}' successfully")
            
        except ConfigurationError as e:
            print(f"❌ {str(e)}")
        except Exception as e:
            print(f"❌ Error deleting profile: {str(e)}")
    
    def show_automation_config(self, scraper: str = None):
        """Show automation configuration"""
        try:
            config = self.config_manager.get_automation_config(scraper)
            
            if scraper:
                print(f"\n⚙️  Automation Config for {scraper.upper()}")
            else:
                print("\n⚙️  Full Automation Configuration")
            
            print("=" * 50)
            print(json.dumps(config, indent=2, default=str))
            
        except Exception as e:
            print(f"❌ Error showing automation config: {str(e)}")
    
    def update_automation_config(self, scraper: str, config_file: Path):
        """Update automation configuration for a scraper"""
        try:
            if not config_file.exists():
                print(f"❌ Configuration file not found: {config_file}")
                return
            
            with open(config_file, 'r') as f:
                new_config = json.load(f)
            
            # Validate configuration
            if not self.config_manager.validate_config(new_config):
                print("❌ Configuration validation failed")
                return
            
            self.config_manager.update_automation_config(scraper, new_config)
            print(f"✅ Updated automation config for {scraper}")
            
        except Exception as e:
            print(f"❌ Error updating automation config: {str(e)}")
    
    def show_merged_config(self, scraper: str, profile: str = None, overrides_file: Path = None):
        """Show merged configuration"""
        try:
            overrides = {}
            if overrides_file and overrides_file.exists():
                with open(overrides_file, 'r') as f:
                    overrides = json.load(f)
            
            merged_config = self.config_manager.get_merged_config(
                scraper=scraper,
                profile=profile,
                overrides=overrides
            )
            
            print(f"\n🔧 Merged Configuration for {scraper.upper()}")
            if profile:
                print(f"   Profile: {profile}")
            if overrides:
                print(f"   Overrides: Applied from {overrides_file}")
            
            print("=" * 50)
            print(json.dumps(merged_config, indent=2, default=str))
            
        except Exception as e:
            print(f"❌ Error showing merged config: {str(e)}")
    
    def export_config(self, output_file: Path):
        """Export all configurations"""
        try:
            self.config_manager.export_config(output_file)
            print(f"✅ Exported configuration to {output_file}")
            
        except Exception as e:
            print(f"❌ Error exporting configuration: {str(e)}")
    
    def import_config(self, input_file: Path):
        """Import configurations"""
        try:
            if not input_file.exists():
                print(f"❌ Configuration file not found: {input_file}")
                return
            
            # Confirm import
            confirm = input(f"Import configuration from {input_file}? This will overwrite existing configs. (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Configuration import cancelled")
                return
            
            self.config_manager.import_config(input_file)
            print(f"✅ Imported configuration from {input_file}")
            
        except Exception as e:
            print(f"❌ Error importing configuration: {str(e)}")
    
    def set_overrides(self, overrides_file: Path):
        """Set global configuration overrides"""
        try:
            if not overrides_file.exists():
                print(f"❌ Overrides file not found: {overrides_file}")
                return
            
            with open(overrides_file, 'r') as f:
                overrides = json.load(f)
            
            self.config_manager.set_overrides(overrides)
            print("✅ Set global configuration overrides")
            
        except Exception as e:
            print(f"❌ Error setting overrides: {str(e)}")
    
    def _interactive_settings_creation(self) -> Dict[str, Any]:
        """Interactive settings creation"""
        print("\n🔧 Interactive Profile Settings Creation")
        print("Press Enter to use default values")
        
        settings = {}
        
        # Basic settings
        max_pages = input("Max pages (default: 10): ").strip()
        if max_pages:
            settings['max_pages'] = int(max_pages)
        
        headless = input("Headless mode (y/N): ").strip().lower()
        if headless == 'y':
            settings['headless'] = True
        
        request_delay = input("Request delay in seconds (default: 2): ").strip()
        if request_delay:
            settings['request_delay'] = int(request_delay)
        
        timeout = input("Timeout in seconds (default: 30): ").strip()
        if timeout:
            settings['timeout'] = int(timeout)
        
        # Advanced settings
        print("\n🔧 Advanced Settings (optional)")
        
        priority_countries = input("Priority countries (comma-separated): ").strip()
        if priority_countries:
            settings['priority_countries'] = [c.strip() for c in priority_countries.split(',')]
        
        min_relevance = input("Minimum relevance score (0-100): ").strip()
        if min_relevance:
            settings['min_relevance_score'] = float(min_relevance)
        
        return settings


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="VisionSeal Configuration Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Profiles commands
    profiles_parser = subparsers.add_parser('profiles', help='Profile management')
    profiles_subparsers = profiles_parser.add_subparsers(dest='profiles_action')
    
    # List profiles
    profiles_subparsers.add_parser('list', help='List all profiles')
    
    # Show profile
    show_profile_parser = profiles_subparsers.add_parser('show', help='Show profile details')
    show_profile_parser.add_argument('name', help='Profile name')
    
    # Create profile
    create_profile_parser = profiles_subparsers.add_parser('create', help='Create new profile')
    create_profile_parser.add_argument('name', help='Profile name')
    create_profile_parser.add_argument('description', help='Profile description')
    create_profile_parser.add_argument('--settings-file', type=Path, help='JSON file with settings')
    
    # Delete profile
    delete_profile_parser = profiles_subparsers.add_parser('delete', help='Delete profile')
    delete_profile_parser.add_argument('name', help='Profile name')
    
    # Automation config commands
    automation_parser = subparsers.add_parser('automation', help='Automation configuration')
    automation_subparsers = automation_parser.add_subparsers(dest='automation_action')
    
    # Show automation config
    show_auto_parser = automation_subparsers.add_parser('show', help='Show automation config')
    show_auto_parser.add_argument('--scraper', choices=['ungm', 'tunipages'], help='Specific scraper')
    
    # Update automation config
    update_auto_parser = automation_subparsers.add_parser('update', help='Update automation config')
    update_auto_parser.add_argument('scraper', choices=['ungm', 'tunipages'], help='Scraper to update')
    update_auto_parser.add_argument('config_file', type=Path, help='JSON configuration file')
    
    # Merged config
    merged_parser = subparsers.add_parser('merged', help='Show merged configuration')
    merged_parser.add_argument('scraper', choices=['ungm', 'tunipages'], help='Scraper')
    merged_parser.add_argument('--profile', help='Profile name')
    merged_parser.add_argument('--overrides', type=Path, help='Overrides file')
    
    # Export/Import
    export_parser = subparsers.add_parser('export', help='Export configuration')
    export_parser.add_argument('output_file', type=Path, help='Output file')
    
    import_parser = subparsers.add_parser('import', help='Import configuration')
    import_parser.add_argument('input_file', type=Path, help='Input file')
    
    # Overrides
    overrides_parser = subparsers.add_parser('overrides', help='Set global overrides')
    overrides_parser.add_argument('overrides_file', type=Path, help='Overrides JSON file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = ConfigCLI()
    
    try:
        if args.command == 'profiles':
            if args.profiles_action == 'list':
                cli.list_profiles()
            elif args.profiles_action == 'show':
                cli.show_profile(args.name)
            elif args.profiles_action == 'create':
                cli.create_profile(args.name, args.description, args.settings_file)
            elif args.profiles_action == 'delete':
                cli.delete_profile(args.name)
            else:
                profiles_parser.print_help()
        
        elif args.command == 'automation':
            if args.automation_action == 'show':
                cli.show_automation_config(args.scraper)
            elif args.automation_action == 'update':
                cli.update_automation_config(args.scraper, args.config_file)
            else:
                automation_parser.print_help()
        
        elif args.command == 'merged':
            cli.show_merged_config(args.scraper, args.profile, args.overrides)
        
        elif args.command == 'export':
            cli.export_config(args.output_file)
        
        elif args.command == 'import':
            cli.import_config(args.input_file)
        
        elif args.command == 'overrides':
            cli.set_overrides(args.overrides_file)
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()