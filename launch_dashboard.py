#!/usr/bin/env python3
"""
Launch VisionSeal web dashboard
"""
import subprocess
import sys
from pathlib import Path

def launch_dashboard():
    """Launch the VisionSeal dashboard"""
    print("🎯 LAUNCHING VISIONSEAL DASHBOARD")
    print("=" * 40)
    print("✅ Web-based African tender opportunities viewer")
    print("✅ Real-time data from Supabase database")
    print("✅ User authentication with sign in/sign up")
    print("✅ Search and filter capabilities")
    print("✅ Guest access available")
    print()
    
    dashboard_dir = Path(__file__).parent / "web_dashboard"
    server_script = dashboard_dir / "server.py"
    
    if not server_script.exists():
        print("❌ Dashboard server script not found")
        return False
    
    try:
        # Launch the dashboard server
        print("🚀 Starting dashboard server...")
        subprocess.run([sys.executable, str(server_script)], cwd=dashboard_dir)
        return True
        
    except KeyboardInterrupt:
        print("\n✅ Dashboard closed")
        return True
    except Exception as e:
        print(f"❌ Failed to launch dashboard: {e}")
        return False

if __name__ == "__main__":
    success = launch_dashboard()
    
    if success:
        print("\n🎉 Dashboard session completed")
        print("📊 Your African tender database is accessible via:")
        print("   • Authentication: http://localhost:8080/auth.html")
        print("   • Protected Dashboard: http://localhost:8080/dashboard.html")
        print("   • Guest Access: http://localhost:8080/index.html")
        print("   • Supabase Console: https://supabase.com/dashboard/project/fycatruiawynbzuafdsx")
    else:
        print("\n📝 Dashboard launch failed")
        print("💡 Try running manually: python web_dashboard/server.py")