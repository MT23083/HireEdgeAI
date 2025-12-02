#!/usr/bin/env python3
"""
Launcher script for the Resume Builder application.

Usage:
    python run_resume_builder.py
    
Or run directly with streamlit:
    streamlit run resume/builder_app.py
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Launch the Resume Builder Streamlit app"""
    
    # Get the path to the builder app
    app_path = Path(__file__).parent / "resume" / "builder_app.py"
    
    if not app_path.exists():
        print(f"Error: Could not find {app_path}")
        sys.exit(1)
    
    print("🚀 Starting Resume Builder...")
    print(f"   App: {app_path}")
    print("")
    print("=" * 50)
    print("  Open http://localhost:8501 in your browser")
    print("=" * 50)
    print("")
    
    # Run streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ])


if __name__ == "__main__":
    main()

