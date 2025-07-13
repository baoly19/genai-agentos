#!/usr/bin/env python3
"""
Script to run all agents by cd'ing to each folder, activating venv, and running with uv.
Follows the exact workflow: cd -> activate venv -> uv run python_file
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
        """Find all agent folders that have both .venv and pyproject.toml"""
        agent_folders = []
        
        if not self.agents_dir.exists():
            print(f"❌ Agents directory {self.agents_dir} does not exist")
            return agent_folders
        
        for item in self.agents_dir.iterdir():
            if (item.is_dir() and 
                (item / ".venv").exists() and 
                (item / "pyproject.toml").exists()):
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
    
    def run_single_agent(self, agent_folder: Path) -> None:
        """Run a single agent following the exact workflow"""
        agent_name = agent_folder.name
        main_file = self.find_main_file(agent_folder)
        
        if not main_file:
            print(f"❌ {agent_name}: No main Python file found")
            return
        
        print(f"🚀 Starting {agent_name}...")
        print(f"   📁 Folder: {agent_folder}")
        print(f"   🐍 File: {main_file.name}")
        
        try:
            # Change to agent directory and run with uv
            # This automatically activates the .venv when using uv run
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
    
    def run_all_agents(self, restart_on_failure: bool = False):
        """Run all agents simultaneously"""
        agent_folders = self.find_agent_folders()
        
        if not agent_folders:
            print("❌ No agent folders found with both .venv and pyproject.toml")
            return
        
        print(f"📁 Found {len(agent_folders)} agent folders:")
        for folder in agent_folders:
            main_file = self.find_main_file(folder)
            print(f"   - {folder.name} → {main_file.name if main_file else 'No main file'}")
        
        print("\n" + "="*60)
        print("🚀 Starting all agents...")
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
            with ThreadPoolExecutor(max_workers=len(agent_folders)) as executor:
                futures = [executor.submit(run_func, folder) for folder in agent_folders]
                
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
    
    print("🤖 GenAI Agent Runner")
    print("=" * 50)
    
    # Ask user for preferences
    restart_mode = input("Enable auto-restart on failure? (y/N): ").lower().strip() == 'y'
    
    print(f"\n🔧 Configuration:")
    print(f"   📁 Agents directory: {agents_dir}")
    print(f"   🔄 Auto-restart: {'Yes' if restart_mode else 'No'}")
    print(f"   💻 Command: uv run <python_file>")
    
    runner.run_all_agents(restart_on_failure=restart_mode)

if __name__ == "__main__":
    main()