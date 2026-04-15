#!/usr/bin/env python
"""
AutoCoder - Autonomous AI Coding Engine
================================
What OpenCode is to the world, AutoCoder is to its users.

Usage:
    python main.py              # Run as API daemon (port 5000)
    python main.py gui        # Run web GUI
    python main.py cli       # Run CLI
    python main.py build    # Build all repos
    python main.py test     # Test all repos
    python main.py push    # Push all to GitHub

AutoCoder is its own commander.
"""

import sys
import os
from pathlib import Path

# Add autocoder to path
AUTOCODER_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOCODER_DIR))

COMMANDS = {
    "gui": "Run web GUI",
    "cli": "Run CLI",
    "api": "Run API daemon",
    "build": "Build all repos",
    "test": "Test all repos", 
    "push": "Push to GitHub",
    "status": "Show status",
    "version": "Show version",
}


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "api"
    
    if cmd == "gui":
        from gui import run_gui
        run_gui()
    
    elif cmd == "api" or cmd == "daemon":
        from daemon import run_server
        run_server()
    
    elif cmd == "cli":
        from cli import run_cli
        run_cli()
    
    elif cmd == "build":
        from build import AutoCoderBuild
        builder = AutoCoderBuild()
        results = builder.build_all()
        for repo, result in results.items():
            print(f"{repo}: {result.status}")
    
    elif cmd == "test":
        from build import AutoCoderBuild
        builder = AutoCoderBuild()
        results = builder.test_all()
        for repo, result in results.items():
            print(f"{repo}: {result.status}")
    
    elif cmd == "push":
        from build import AutoCoderBuild
        builder = AutoCoderBuild()
        results = builder.push_all("pushed by Nrupal built with autocoder")
        for repo, result in results.items():
            print(f"{repo}: {result.status}")
    
    elif cmd == "status":
        from version import get_all_versions
        print("AutoCoder Status:")
        print(f"  Version: {get_all_versions().get('autocoder', '0.1.0')}")
        print(f"  Repos: {list(get_all_versions().keys())}")
    
    elif cmd == "version":
        from version import get_all_versions
        print(f"autocoder: {get_all_versions().get('autocoder', '0.1.0')}")
    
    elif cmd == "help":
        print("AutoCoder Commands:")
        for c, d in COMMANDS.items():
            print(f"  {c:10} - {d}")
    
    else:
        print(f"Unknown command: {cmd}")
        print("Run 'python main.py help' for available commands")
        sys.exit(1)


if __name__ == "__main__":
    main()