#!/usr/bin/env python3
"""
Script to run all agents by cd'ing to each folder, creating venv, installing deps, and running with uv.
Workflow: cd -> create venv -> install deps -> uv run python_file
"""

import os
import subprocess
import sys
import signal
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict
import threading

class AgentRunner:
    def __init__(self, agents_dir: Path):
        self.agents_dir = agents_dir
        self.processes: Dict[str, subprocess.Popen] = {}
        self.should_stop = threading.Event()
        
    def find_agent_folders(self) -> List[Path]:
        """Find all agent folders that have pyproject.toml"""
        agent_folders = []
        
        if not self.agents_dir.exists():
            print(f"❌ Agents directory {self.agents_dir} does not exist")
            return agent_folders
        
        for item in self.agents_dir.iterdir():
            if (item.is_dir() and (item / "pyproject.toml").exists()):
                agent_folders.append(item)
        
        return agent_folders
    
    def find_main_file(self, agent_folder: Path) -> Optional[Path]:
        """Find the main Python file in an agent folder"""
        agent_name = agent_folder.name
        
        # Common patterns for main files
        possible_files = [
            "main.py",
            f"{agent_name}.py",
            "agent.py",
        ]
        
        for filename in possible_files:
            main_file = agent_folder / filename
            if main_file.exists():
                return main_file
        
        # If no common pattern found, look for any .py file
        py_files = [f for f in agent_folder.glob("*.py") if f.is_file()]
        if py_files:
            return py_files[0]  # Return the first .py file found
        
        return None
    
    def setup_agent_environment(self, agent_folder: Path) -> bool:
        """Set up virtual environment and install dependencies for an agent"""
        agent_name = agent_folder.name
        venv_path = agent_folder / ".venv"
        
        try:
            # Check if .venv already exists
            if not venv_path.exists():
                print(f"📦 Creating virtual environment for {agent_name}...")
                result = subprocess.run(
                    ["uv", "venv", ".venv"],
                    cwd=agent_folder,
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(f"✅ Created .venv for {agent_name}")
            else:
                print(f"✅ Virtual environment already exists for {agent_name}")
            
            # Install dependencies using uv sync
            print(f"📥 Installing dependencies for {agent_name}...")
            result = subprocess.run(
                ["uv", "sync"],
                cwd=agent_folder,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✅ Dependencies installed for {agent_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to setup environment for {agent_name}")
            print(f"   Error: {e.stderr if e.stderr else e.stdout}")
            return False
        except FileNotFoundError:
            print(f"❌ 'uv' command not found. Please install uv first.")
            print("   Install: curl -LsSf https://astral.sh/uv/install.sh | sh")
            return False
        except Exception as e:
            print(f"❌ Unexpected error setting up {agent_name}: {e}")
            return False
    
    def run_single_agent(self, agent_folder: Path) -> None:
        """Run a single agent following the complete workflow"""
        agent_name = agent_folder.name
        main_file = self.find_main_file(agent_folder)
        
        if not main_file:
            print(f"❌ {agent_name}: No main Python file found")
            return
        
        print(f"\n🚀 Processing {agent_name}...")
        print(f"   📁 Folder: {agent_folder}")
        print(f"   🐍 File: {main_file.name}")
        
        # Step 1: Setup environment
        if not self.setup_agent_environment(agent_folder):
            print(f"❌ {agent_name}: Environment setup failed, skipping...")
            return
        
        # Step 2: Run the agent
        print(f"🏃 Running {agent_name}...")
        
        try:
            # Change to agent directory and run with uv
            process = subprocess.Popen(
                ["uv", "run", main_file.name],
                cwd=agent_folder,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes[agent_name] = process
            
            # Stream output with agent name prefix
            try:
                while not self.should_stop.is_set():
                    line = process.stdout.readline()
                    if line:
                        print(f"[{agent_name}] {line.rstrip()}")
                    elif process.poll() is not None:
                        break
                    
                # Get any remaining output
                remaining_output = process.stdout.read()
                if remaining_output:
                    for line in remaining_output.splitlines():
                        print(f"[{agent_name}] {line}")
                        
            except Exception as e:
                print(f"❌ {agent_name} output error: {e}")
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code != 0:
                print(f"❌ {agent_name} exited with code {return_code}")
            else:
                print(f"✅ {agent_name} completed successfully")
                
        except FileNotFoundError:
            print(f"❌ {agent_name}: 'uv' command not found. Please install uv first.")
        except Exception as e:
            print(f"❌ {agent_name} error: {e}")
        finally:
            if agent_name in self.processes:
                del self.processes[agent_name]
    
    def run_single_agent_with_restart(self, agent_folder: Path) -> None:
        """Run a single agent with automatic restart on failure"""
        agent_name = agent_folder.name
        
        while not self.should_stop.is_set():
            try:
                self.run_single_agent(agent_folder)
                
                if not self.should_stop.is_set():
                    print(f"⚠️  {agent_name} stopped unexpectedly, restarting in 5 seconds...")
                    for i in range(5):
                        if self.should_stop.is_set():
                            break
                        time.sleep(1)
                        
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ {agent_name} unexpected error: {e}")
                if not self.should_stop.is_set():
                    print(f"⚠️  Restarting {agent_name} in 5 seconds...")
                    for i in range(5):
                        if self.should_stop.is_set():
                            break
                        time.sleep(1)
    
    def stop_all_agents(self):
        """Stop all running agents"""
        print("\n🛑 Stopping all agents...")
        self.should_stop.set()
        
        for agent_name, process in self.processes.items():
            try:
                print(f"   Stopping {agent_name}...")
                process.terminate()
                
                # Wait up to 5 seconds for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"   Force killing {agent_name}...")
                    process.kill()
                    process.wait()
                    
            except Exception as e:
                print(f"   Error stopping {agent_name}: {e}")
    
    def check_prerequisites(self) -> bool:
        """Check if uv is installed"""
        try:
            result = subprocess.run(
                ["uv", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✅ uv is installed: {result.stdout.strip()}")
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("❌ 'uv' is not installed or not working")
            print("💡 Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
            return False
    
    def setup_all_environments_first(self, agent_folders: List[Path]) -> List[Path]:
        """Setup environments for all agents first, return list of successful ones"""
        print("🔧 ENVIRONMENT SETUP PHASE")
        print("=" * 40)
        
        successful_agents = []
        
        for agent_folder in agent_folders:
            agent_name = agent_folder.name
            print(f"\n📦 Setting up {agent_name}...")
            
            if self.setup_agent_environment(agent_folder):
                successful_agents.append(agent_folder)
                print(f"✅ {agent_name} ready to run")
            else:
                print(f"❌ {agent_name} setup failed, will be skipped")
        
        print(f"\n📊 Setup Results: {len(successful_agents)}/{len(agent_folders)} agents ready")
        return successful_agents
    
    def run_all_agents(self, restart_on_failure: bool = False, setup_first: bool = True):
        """Run all agents simultaneously"""
        # Check prerequisites
        if not self.check_prerequisites():
            return
        
        agent_folders = self.find_agent_folders()
        
        if not agent_folders:
            print("❌ No agent folders found with pyproject.toml")
            print("💡 Make sure you're in the cli/ directory and agents exist")
            return
        
        print(f"📁 Found {len(agent_folders)} agent folders:")
        for folder in agent_folders:
            main_file = self.find_main_file(folder)
            print(f"   - {folder.name} → {main_file.name if main_file else 'No main file'}")
        
        # Setup environments first if requested
        if setup_first:
            ready_agents = self.setup_all_environments_first(agent_folders)
            if not ready_agents:
                print("❌ No agents are ready to run")
                return
        else:
            ready_agents = agent_folders
        
        print("\n" + "="*60)
        print("🚀 AGENT EXECUTION PHASE")
        print("="*60)
        print(f"Running {len(ready_agents)} agents...")
        if restart_on_failure:
            print("🔄 Auto-restart mode enabled")
        print("Press Ctrl+C to stop all agents")
        print("="*60 + "\n")
        
        # Set up signal handler for graceful shutdown
        def signal_handler(signum, frame):
            self.stop_all_agents()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Choose the run function based on restart preference
        run_func = self.run_single_agent_with_restart if restart_on_failure else self.run_single_agent
        
        # Run all agents in parallel using ThreadPoolExecutor
        try:
            with ThreadPoolExecutor(max_workers=len(ready_agents)) as executor:
                futures = [executor.submit(run_func, folder) for folder in ready_agents]
                
                # Wait for all agents to complete
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"❌ Agent thread error: {e}")
                        
        except KeyboardInterrupt:
            self.stop_all_agents()
        
        print("\n✅ All agents stopped")

def main():
    """Main function"""
    script_dir = Path(__file__).parent
    agents_dir = script_dir / "agents"
    
    runner = AgentRunner(agents_dir)
    
    print("🤖 GenAI Agent Runner - Complete Setup & Execution")
    print("=" * 60)
    print("This script will:")
    print("1. 🔍 Find all agent folders")
    print("2. 📦 Create virtual environments (.venv)")
    print("3. 📥 Install dependencies (uv sync)")
    print("4. 🚀 Run all agents simultaneously")
    print("=" * 60 + "\n")
    
    # Ask user for preferences
    restart_mode = input("Enable auto-restart on failure? (y/N): ").lower().strip() == 'y'
    setup_first = input("Setup environments before running? (Y/n): ").lower().strip() != 'n'
    
    print(f"\n🔧 Configuration:")
    print(f"   📁 Agents directory: {agents_dir}")
    print(f"   🔄 Auto-restart: {'Yes' if restart_mode else 'No'}")
    print(f"   📦 Setup first: {'Yes' if setup_first else 'No'}")
    print(f"   💻 Command: uv run <python_file>")
    
    runner.run_all_agents(restart_on_failure=restart_mode, setup_first=setup_first)

if __name__ == "__main__":
    main()