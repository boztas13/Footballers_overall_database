#!/usr/bin/env python3
"""
Football Scout Dashboard Launcher
Run this script to start the Streamlit dashboard
"""

import subprocess
import sys
import os
import time

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['streamlit', 'pandas', 'numpy', 'plotly', 'sqlite3']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("📦 Installing missing packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
        print("✅ All packages installed successfully!")
    
    return len(missing_packages) == 0

def check_database():
    """Check if database exists"""
    db_path = "data/statsbomb.db"
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        print("📊 Please run 'python map_stats_bomb_db.py' first to create the database")
        return False
    
    print("✅ Database found!")
    return True

def main():
    """Main launcher function"""
    print("🚀 Football Scout Dashboard Launcher")
    print("="*50)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    check_dependencies()
    
    # Check database
    print("🗄️ Checking database...")
    if not check_database():
        return
    
    print("🎯 Starting Football Scout Dashboard...")
    print("🌐 Dashboard will open at: http://localhost:8501")
    print("⏹️  Press Ctrl+C to stop the dashboard")
    print("="*50)
    
    try:
        # Start Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "football_dashboard.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

if __name__ == "__main__":
    main()
