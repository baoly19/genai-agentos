#!/usr/bin/env python3
"""
Script to update AGENT_JWT tokens in all agent files at once.
"""

import os
import re
from pathlib import Path

def update_jwt_in_file(file_path: Path, new_jwt: str) -> bool:
    """Update JWT token in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern 1: AGENT_JWT = "old_token"
        pattern1 = r'AGENT_JWT = "eyJ[^"]*"'
        replacement1 = f'AGENT_JWT = "{new_jwt}"'
        
        # Pattern 2: jwt_token="old_token" (direct in session)
        pattern2 = r'jwt_token="eyJ[^"]*"'
        replacement2 = f'jwt_token="{new_jwt}"'
        
        # Apply replacements
        new_content = re.sub(pattern1, replacement1, content)
        new_content = re.sub(pattern2, replacement2, new_content)
        
        # Only write if content changed
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        return False
        
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    """Main function to update all agent JWT tokens."""
    
    # Get the new JWT token from user
    print("🔑 JWT Token Updater for All Agents")
    print("=" * 50)
    
    new_jwt = input("Enter the new JWT token: ").strip()
    
    if not new_jwt:
        print("❌ No JWT token provided. Exiting.")
        return
    
    if not new_jwt.startswith("eyJ"):
        print("⚠️  Warning: JWT token doesn't start with 'eyJ'. Are you sure this is correct?")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Aborted.")
            return
    
    # Define agent files to update
    agent_files = [
        "agents/analyzer/analyzer.py",
        "agents/diagnosis_reasoner/diagnosis_reasoner.py", 
        "agents/get_current_date_agent/main.py",
        "agents/get_image_and_upload_mcp/get_image_and_upload_mcp.py",
        "agents/get_weather_agent/main.py",
        "agents/medical_image_interpreter/medical_image_interpreter.py",
        "agents/ocr_lab_test_result/ocr_lab_test_result.py",
        "agents/search_pubmed_abstracts/search_pubmed_abstracts.py",
        "agents/treatment_recommender/treatment_recommender.py"
    ]
    
    print(f"\n📝 Updating JWT tokens in {len(agent_files)} files...")
    print("-" * 50)
    
    updated_count = 0
    script_dir = Path(__file__).parent
    
    for file_path_str in agent_files:
        file_path = script_dir / file_path_str
        
        if not file_path.exists():
            print(f"⚠️  {file_path_str} - File not found, skipping")
            continue
        
        if update_jwt_in_file(file_path, new_jwt):
            print(f"✅ {file_path_str} - Updated successfully")
            updated_count += 1
        else:
            print(f"ℹ️  {file_path_str} - No changes needed or failed")
    
    print("-" * 50)
    print(f"🎉 Updated {updated_count} files successfully!")
    
    if updated_count > 0:
        print("\n💡 Next steps:")
        print("1. Verify the changes look correct")
        print("2. Test your agents to make sure they work with the new JWT")
        print("3. Run: genai run_agents")

if __name__ == "__main__":
    main() 