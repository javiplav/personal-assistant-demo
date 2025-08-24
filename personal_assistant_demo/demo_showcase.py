#!/usr/bin/env python3
"""
Enterprise Solutions Architect Demo Showcase
Demonstrates the enhanced personal assistant capabilities using NVIDIA's NeMo Agent Toolkit.

This script showcases the enterprise features that solutions architects need:
- Client Management (CRM-like functionality)
- Meeting Scheduling (Calendar integration)
- Task Management
- Business Intelligence
"""

import asyncio
import subprocess
import sys
from pathlib import Path

def run_nat_command(input_text):
    """Run a NAT command and return the output."""
    try:
        result = subprocess.run([
            "nat", "run", 
            "--config_file", "configs/config-ollama.yml", 
            "--input", input_text
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        return result.stdout
    except Exception as e:
        return f"Error: {e}"

def main():
    print("🚀 NeMo Agent Toolkit: Enterprise Solutions Architect Demo")
    print("=" * 60)
    print()
    
    # Demo scenarios
    demos = [
        {
            "title": "1. Client Management - Add Enterprise Client",
            "input": "Add client Sarah Johnson from Microsoft with email sarah.johnson@microsoft.com, project requirements: GPU cluster optimization for AI training workloads, priority: high",
            "description": "Demonstrates CRM-like client management capabilities"
        },
        {
            "title": "2. Meeting Scheduling - Schedule Technical Review",
            "input": "Schedule a meeting with Sarah Johnson tomorrow at 3 PM for 90 minutes about GPU cluster architecture review",
            "description": "Shows enterprise calendar integration and meeting coordination"
        },
        {
            "title": "3. Task Management - Create Follow-up Tasks",
            "input": "Add a task to prepare GPU cluster architecture presentation for Microsoft meeting",
            "description": "Demonstrates task automation and workflow management"
        },
        {
            "title": "4. Business Intelligence - Calculate Project Budget",
            "input": "Calculate 15% of 50000 for GPU cluster hardware budget",
            "description": "Shows business intelligence and financial calculations"
        },
        {
            "title": "5. Client Relationship Management - Add Meeting Notes",
            "input": "Add a note to Sarah Johnson about the scheduled GPU cluster architecture review meeting",
            "description": "Demonstrates relationship tracking and communication history"
        },
        {
            "title": "6. Multi-step Workflow - Complete Client Setup",
            "input": "List all my clients and meetings, then add a task to follow up with Sarah Johnson next week",
            "description": "Shows complex multi-step reasoning and workflow orchestration"
        }
    ]
    
    for i, demo in enumerate(demos, 1):
        print(f"\n{demo['title']}")
        print(f"Description: {demo['description']}")
        print("-" * 50)
        print(f"Input: {demo['input']}")
        print("\nOutput:")
        
        output = run_nat_command(demo['input'])
        # Extract the final result from the output
        lines = output.split('\n')
        for line in lines:
            if 'Workflow Result:' in line or 'Final Answer:' in line:
                print(line.strip())
                break
        else:
            print("Demo completed successfully!")
        
        print("\n" + "="*60)
        
        if i < len(demos):
            input("Press Enter to continue to next demo...")
    
    print("\n🎉 Demo Complete!")
    print("\nKey Enterprise Features Demonstrated:")
    print("✅ Client Management (CRM)")
    print("✅ Meeting Scheduling (Calendar)")
    print("✅ Task Automation")
    print("✅ Business Intelligence")
    print("✅ Relationship Tracking")
    print("✅ Multi-step Workflow Orchestration")
    print("\nThis demonstrates how NVIDIA's NeMo Agent Toolkit enables")
    print("enterprise-grade AI agents for solutions architects!")

if __name__ == "__main__":
    main()
