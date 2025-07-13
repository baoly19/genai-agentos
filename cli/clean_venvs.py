#!/usr/bin/env python3
"""
Simple script to remove all .venv folders from agent subfolders.
Use this to test the environment setup from scratch.
"""

import shutil
import sys
from pathlib import Path

def remove_venv_folders(agents_dir: Path):
    """Remove all .venv folders from agent subfolders"""
    
    if not agents_dir.exists():
        print(f"❌ Directory {agents_dir} does not exist")
        return
    
    print(f"🔍 Scanning {agents_dir} for .venv folders...")
    
    removed_count = 0
    total_agents = 0
    
    for item in agents_dir.iterdir():
        if item.is_dir():
            total_agents += 1
            venv_path = item / ".venv"
            
            if venv_path.exists():
                try:
                    print(f"🗑️  Removing .venv from {item.name}...")
                    shutil.rmtree(venv_path)
                    print(f"✅ Removed .venv from {item.name}")
                    removed_count += 1
                except Exception as e:
                    print(f"❌ Failed to remove .venv from {item.name}: {e}")
            else:
                print(f"ℹ️  No .venv found in {item.name}")
    
    print(f"\n📊 Summary:")
    print(f"   Total agent folders: {total_agents}")
    print(f"   .venv folders removed: {removed_count}")
    print(f"   Ready for fresh setup! 🚀")

def main():
    """Main function"""
    script_dir = Path(__file__).parent
    agents_dir = script_dir / "agents"
    
    print("🧹 GenAI Agent .venv Cleaner")
    print("=" * 40)
    print(f"Target directory: {agents_dir}")
    print("This will remove all .venv folders from agent subfolders.")
    print("=" * 40 + "\n")
    
    # Confirm with user
    confirm = input("Are you sure you want to remove all .venv folders? (y/N): ").lower().strip()
    
    if confirm == 'y':
        remove_venv_folders(agents_dir)
    else:
        print("❌ Operation cancelled")

if __name__ == "__main__":
    main() 