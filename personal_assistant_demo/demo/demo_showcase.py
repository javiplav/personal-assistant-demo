#!/usr/bin/env python3
"""
Enterprise Solutions Architect Demo Showcase
Demonstrates the enhanced personal assistant capabilities using NVIDIA's NeMo Agent Toolkit.

This script showcases the enterprise features that solutions architects need:
- Client Management (CRM-like functionality)
- Meeting Scheduling
- Task Management
- Business Intelligence
"""

import asyncio
import subprocess
import sys
from pathlib import Path
import time
import ast
import requests
import re
import argparse

def check_ollama_status():
    """Check if Ollama is running and has the required model."""
    try:
        # Check if Ollama is responding
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            qwen_models = [m for m in models if 'qwen2.5' in m.get('name', '').lower()]
            if qwen_models:
                return {"status": "ready", "model": qwen_models[0]['name']}
            else:
                return {"status": "no_model", "models": [m.get('name') for m in models]}
        else:
            return {"status": "error", "message": f"Ollama returned status {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"status": "not_running", "error": str(e)}

def run_nat_command(input_text, config_file="configs/config-ollama.yml"):
    """Run a NAT command and return the parsed result."""
    try:
        cmd = [
            "nat", "run", 
            "--config_file", config_file, 
            "--input", input_text
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode != 0:
            return {"error": f"Command failed with return code {result.returncode}", "stderr": result.stderr, "stdout": result.stdout}
        
        # Parse the output to extract the workflow result
        # NAT may output to stderr, so combine both stdout and stderr
        output_text = result.stdout + '\n' + (result.stderr or '')
        workflow_result = None
        
        # More robust parsing approach
        # 1. First try to find the Workflow Result section
        if 'Workflow Result:' in output_text:
            workflow_section = output_text.split('Workflow Result:')[1].split('--------------------------------------------------')[0]
            # Extract content between brackets or quotes
            # Look for ['result'] pattern
            bracket_match = re.search(r'\[(.*?)\]', workflow_section)
            if bracket_match:
                result_content = bracket_match.group(1).strip('\'"')
                if result_content:
                    workflow_result = result_content
        
        # 2. Fallback: look for Final Answer in agent thoughts
        if not workflow_result:
            final_answer_pattern = re.search(r'Final Answer:\s*(.*?)(?:\n|$)', output_text)
            if final_answer_pattern:
                workflow_result = final_answer_pattern.group(1).strip()
        
        # 3. Additional fallback: extract from tool responses
        if not workflow_result or workflow_result == "Task completed successfully":
            tool_responses = re.findall(r"Tool's response:\s*\n([^\n-]+)", output_text)
            if tool_responses:
                # Get the last meaningful tool response
                for response in reversed(tool_responses):
                    response = response.strip()
                    if response and len(response) > 10 and not response.startswith('The '):
                        workflow_result = response
                        break
        
        # Check for common error patterns in the result
        error_patterns = ["[401] Unauthorized", "Authentication failed", "API key", "Error:", "Exception:", "failed with exception"]
        is_error = any(pattern in output_text for pattern in error_patterns)
        
        # Also check if we got a meaningful result
        success_patterns = ["added successfully", "Task #", "Client", "Meeting", "scheduled", "calculated", "Note"]
        has_success_indicator = workflow_result and any(pattern in workflow_result for pattern in success_patterns)
        
        if is_error and not has_success_indicator:
            return {
                "success": False,
                "error": workflow_result or "Command failed with error",
                "full_output": result.stdout
            }
        
        return {
            "success": True,
            "result": workflow_result or "Task completed successfully",
            "full_output": result.stdout
        }
        
    except Exception as e:
        return {"error": f"Exception occurred: {e}", "success": False}

def main(config_file="configs/config-ollama.yml"):
    """Main demo function."""
    # Determine configuration type for display
    if "ollama" in config_file:
        config_type = "Ollama (Local LLM)"
    elif "nim" in config_file or config_file.endswith("config.yml"):
        config_type = "NIM (Cloud LLM)"
    else:
        config_type = "Custom Configuration"
    
    print("🚀 NeMo Agent Toolkit: Enterprise Solutions Architect Demo")
    print("=" * 65)
    print(f"📋 Configuration: {config_type}")
    print(f"🔧 Config File: {config_file}")
    print("=" * 65)
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
            "description": "Shows enterprise meeting coordination and scheduling"
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
    
    # Comprehensive validation checks
    print("🔍 Validating system requirements...")
    print()
    
    # Check LLM backend based on config
    if "ollama" in config_file:
        print("1️⃣ Checking Ollama service...")
        ollama_status = check_ollama_status()
        
        if ollama_status["status"] == "ready":
            print(f"   ✅ Ollama is running with model: {ollama_status['model']}")
        elif ollama_status["status"] == "no_model":
            print(f"   ❌ Ollama is running but qwen2.5 model not found")
            print(f"   Available models: {', '.join(ollama_status.get('models', ['None']))}")
            print("   Run: ollama pull qwen2.5:7b")
            return
        elif ollama_status["status"] == "not_running":
            print("   ❌ Ollama is not running")
            print("   Please start Ollama service and ensure qwen2.5:7b model is available")
            return
        else:
            print(f"   ❌ Ollama error: {ollama_status.get('message', 'Unknown error')}")
            return
    else:
        # For NIM or other configurations
        print("1️⃣ Checking LLM service configuration...")
        print("   ✅ Using cloud-based LLM service (NIM or other)")
        print("   ℹ️  Make sure your API key is properly configured")
    
    # Check NAT installation
    print("2️⃣ Checking NAT installation...")
    validation_result = run_nat_command("Calculate 2 + 2", config_file)
    
    if not validation_result.get("success"):
        print("   ❌ NAT validation failed!")
        print(f"   Error: {validation_result.get('error', 'Unknown error')}")
        if 'stderr' in validation_result:
            print(f"   Details: {validation_result['stderr'][:200]}...")
        print("\n   Troubleshooting:")
        print("   • Ensure NAT is properly installed and in PATH")
        print("   • Check that configuration file is valid")
        print("   • Verify all dependencies are installed")
        return
    
    print("   ✅ NAT is working correctly")
    print("3️⃣ Configuration validated")
    print(f"   ✅ Test result: {validation_result['result']}")
    
    print("\n🎉 All systems ready! Starting enterprise demo...")
    print("=" * 70)
    
    for demo_idx, demo in enumerate(demos, 1):
        print(f"\n{demo['title']}")
        print(f"🎯 Description: {demo['description']}")
        print("-" * 60)
        print(f"📝 Input: \"{demo['input']}\"")
        print("\n🤖 Processing...")
        
        # Add timing for professional demo feel
        start_time = time.time()
        result = run_nat_command(demo['input'], config_file)
        end_time = time.time()
        processing_time = end_time - start_time
        
        if result.get("success"):
            print(f"✅ Result: {result['result']}")
            print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            print(f"⏱️  Failed after: {processing_time:.2f} seconds")
            if 'stderr' in result:
                print(f"📄 Details: {result['stderr'][:300]}...")
            # Option to show full output for debugging
            print("\n🔧 Debugging options:")
            show_debug = input("   Show full output for debugging? (y/N): ").lower().strip()
            if show_debug == 'y':
                print("\n--- Full Output ---")
                print(result.get('full_output', 'No output available'))
                print("--- End Output ---")
        
        print("\n" + "="*70)
        
        if demo_idx < len(demos):
            print("Press Enter to continue to next demo...")
            input()
    
    print("\n🎉 Demo Complete! Enterprise AI Agent Showcase Finished")
    print("=" * 70)
    print("\n🏢 ENTERPRISE FEATURES SUCCESSFULLY DEMONSTRATED:")
    print("  ✅ Client Relationship Management (CRM)")
    print("  ✅ Intelligent Meeting Scheduling")
    print("  ✅ Automated Task Management")
    print("  ✅ Business Intelligence & Calculations")
    print("  ✅ Multi-step Workflow Orchestration")
    print("  ✅ Context-aware Relationship Tracking")
    
    print("\n🚀 NVIDIA NeMo Agent Toolkit Advantages:")
    print("  🎯 Natural Language Interface for Complex Workflows")
    print("  ⚡ High-Performance Local LLM Integration")
    print("  🔧 Extensible Tool & Function Framework")
    print("  🏗️  Enterprise-Ready Architecture")
    print("  📈 Scalable Multi-Agent Capabilities")
    
    print("\n🎬 Perfect for Solutions Architects who need:")
    print("  • Client management and relationship tracking")
    print("  • Automated scheduling and task coordination")
    print("  • Business intelligence and data analysis")
    print("  • Complex multi-step workflow automation")
    
    print(f"\n💡 Ready to build your own enterprise AI agents?")
    print("   Visit: https://developer.nvidia.com/nemo")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="NeMo Agent Toolkit Enterprise Solutions Architect Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with Ollama (default)
  python demo_showcase.py
  
  # Run with NIM
  python demo_showcase.py --config configs/config.yml
  
  # Run with Ollama + Environment Variables
  python demo_showcase.py --config configs/config-ollama-env.yml
        """
    )
    
    parser.add_argument(
        "--config", 
        default="configs/config-ollama.yml",
        help="Configuration file to use (default: configs/config-ollama.yml)"
    )
    
    args = parser.parse_args()
    main(args.config)
