#!/usr/bin/env python3
"""
Simple script to register all agents and update their JWT tokens.
Handles existing agents to avoid duplicates.
"""

import asyncio
import re
import sys
from pathlib import Path
from uuid import uuid4
import httpx
from typing import Optional, List, Dict

# Add the CLI src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Agent definitions
AGENTS = {
    "analyzer": "Extract structured triage information from the patient's free-text input. This includes age, gender, relevant medical history, current symptoms, duration, severity, and an overall triage level.",
    "diagnosis_reasoner": "Suggest 1–3 likely diagnoses based on structured patient triage data and lab test results with justifications.",
    "get_image_and_upload_mcp": "Get image and upload to ai mcp server",
    "ocr_lab_test_result": "agent to extract information from lab report pdf",
    "search_pubmed_abstracts": "Search abstracts in PubMed and return a list of articles",
    "treatment_recommender": "Generate a treatment plan for the most likely diagnosis, including medication, dosage, lifestyle suggestions, and medical cautions."
}

# Simple HTTP client functions
async def login_user(username: str, password: str, base_url: str = "http://localhost:8000") -> Optional[str]:
    """Login user and return JWT token"""
    async with httpx.AsyncClient(base_url=base_url) as client:
        response = await client.post(
            "/api/login/access-token",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"❌ Login failed: {response.status_code}")
            return None

async def get_existing_agents(jwt_token: str, base_url: str = "http://localhost:8000") -> List[Dict]:
    """Get list of existing agents"""
    async with httpx.AsyncClient(base_url=base_url) as client:
        headers = {"Authorization": f"Bearer {jwt_token}"}
        response = await client.get("/api/agents/", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get existing agents: {response.status_code}")
            return []

async def register_agent_api(agent_id: str, name: str, description: str, jwt_token: str, base_url: str = "http://localhost:8000") -> Optional[str]:
    """Register agent and return agent JWT token"""
    async with httpx.AsyncClient(base_url=base_url) as client:
        headers = {"Authorization": f"Bearer {jwt_token}"}
        response = await client.post(
            "/api/agents/register",
            json={
                "id": agent_id,
                "name": name,
                "description": description,
                "input_parameters": {},
            },
            headers=headers
        )
        if response.status_code == 200:
            return response.json().get("jwt")
        else:
            print(f"❌ Failed to register {name}: {response.status_code}")
            if response.status_code == 400:
                error_text = response.text
                if "already exists" in error_text:
                    print(f"   Agent {name} already exists")
                else:
                    print(f"   Error: {error_text}")
            return None

def load_user_jwt() -> Optional[str]:
    """Load user JWT from credentials file"""
    try:
        creds_file = Path.home() / ".genai" / "credentials"
        if creds_file.exists():
            with open(creds_file, 'r') as f:
                return f.read().strip()
    except Exception:
        pass
    return None

def update_jwt_token(agent_name: str, jwt_token: str):
    """Update JWT token in agent file"""
    agents_dir = Path(__file__).parent / "agents"
    agent_folder = agents_dir / agent_name
    
    # Find the Python file
    possible_files = [
        agent_folder / "main.py",
        agent_folder / f"{agent_name}.py",
    ]
    
    main_file = None
    for file_path in possible_files:
        if file_path.exists():
            main_file = file_path
            break
    
    if not main_file:
        # Look for any .py file
        py_files = list(agent_folder.glob("*.py"))
        if py_files:
            main_file = py_files[0]
    
    if not main_file:
        print(f"❌ No Python file found for {agent_name}")
        return False
    
    try:
        # Read file
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update JWT token
        patterns = [
            (r'AGENT_JWT = "eyJ[^"]*"', f'AGENT_JWT = "{jwt_token}"'),
            (r'jwt_token="eyJ[^"]*"', f'jwt_token="{jwt_token}"')
        ]
        
        updated = False
        for pattern, replacement in patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                updated = True
        
        if updated:
            # Write back
            with open(main_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated JWT for {agent_name}")
            return True
        else:
            print(f"⚠️  No JWT pattern found in {agent_name}")
            return False
        
    except Exception as e:
        print(f"❌ Error updating {agent_name}: {e}")
        return False

def find_existing_agent_by_name(existing_agents: List[Dict], agent_name: str) -> Optional[Dict]:
    """Find existing agent by name"""
    for agent in existing_agents:
        if agent.get("agent_name") == agent_name:
            return agent
    return None

async def main():
    """Main function"""
    print("🤖 Smart Agent Registration & JWT Update")
    print("=" * 50)
    
    # Check if user is logged in
    user_jwt = load_user_jwt()
    if not user_jwt:
        print("❌ No user JWT found. Please login first:")
        print("   genai login -u <username>")
        print("\nOr login now:")
        username = input("Username: ").strip()
        if not username:
            return
        
        import getpass
        password = getpass.getpass("Password: ")
        
        user_jwt = await login_user(username, password)
        if not user_jwt:
            return
        
        # Save JWT to credentials file
        try:
            creds_dir = Path.home() / ".genai"
            creds_dir.mkdir(exist_ok=True)
            with open(creds_dir / "credentials", 'w') as f:
                f.write(user_jwt)
            print("✅ Logged in successfully!")
        except Exception as e:
            print(f"⚠️  Warning: Could not save credentials: {e}")
    
    # Get existing agents
    print("\n🔍 Checking existing agents...")
    existing_agents = await get_existing_agents(user_jwt)
    
    if existing_agents:
        print(f"📋 Found {len(existing_agents)} existing agents:")
        for agent in existing_agents:
            print(f"   - {agent.get('agent_name', 'Unknown')}")
    else:
        print("📋 No existing agents found")
    
    registered = 0
    updated = 0
    skipped = 0
    
    print(f"\n🚀 Processing {len(AGENTS)} agents...")
    
    for agent_name, description in AGENTS.items():
        print(f"\n📝 Processing: {agent_name}")
        
        # Check if agent already exists
        existing_agent = find_existing_agent_by_name(existing_agents, agent_name)
        
        if existing_agent:
            print(f"ℹ️  Agent {agent_name} already exists")
            
            # Ask user what to do
            choice = input(f"   What to do? (s)kip, (u)pdate JWT only, (r)egister new: ").lower().strip()
            
            if choice == 's':
                print(f"⏭️  Skipped: {agent_name}")
                skipped += 1
                continue
            elif choice == 'u':
                # Use existing agent's JWT
                existing_jwt = existing_agent.get("agent_jwt")
                if existing_jwt and update_jwt_token(agent_name, existing_jwt):
                    updated += 1
                    print(f"✅ Updated JWT for existing agent: {agent_name}")
                else:
                    print(f"❌ Failed to update JWT for: {agent_name}")
                continue
            elif choice == 'r':
                print(f"🔄 Will register new agent with same name: {agent_name}")
                # Continue to registration
            else:
                print(f"⏭️  Invalid choice, skipping: {agent_name}")
                skipped += 1
                continue
        
        # Register new agent
        agent_jwt = await register_agent_api(
            agent_id=str(uuid4()),
            name=agent_name,
            description=description,
            jwt_token=user_jwt
        )
        
        if agent_jwt:
            print(f"✅ Registered: {agent_name}")
            registered += 1
            
            # Update JWT token in file
            if update_jwt_token(agent_name, agent_jwt):
                updated += 1
        else:
            print(f"❌ Failed to register: {agent_name}")
    
    print(f"\n📊 Results:")
    print(f"   ✅ Registered: {registered}")
    print(f"   🔄 Updated: {updated}")
    print(f"   ⏭️  Skipped: {skipped}")
    print(f"   📁 Total: {len(AGENTS)}")
    
    if registered > 0 or updated > 0:
        print(f"\n🚀 Ready to run agents:")
        print(f"   python run_all_agents.py")

if __name__ == "__main__":
    asyncio.run(main())