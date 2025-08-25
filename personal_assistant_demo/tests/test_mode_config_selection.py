#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Test to verify that mode selection correctly loads the appropriate configuration files.
This ensures that explicit user choices for "tool-calling" and "react" modes 
load the correct NIM configuration files.
"""

import sys
from pathlib import Path

# Add the src directory to Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_assistant.web_server import WebServer


def test_nim_tool_calling_config_selection():
    """Test that selecting 'tool-calling' mode with 'nim' model loads the correct config."""
    print("🧪 Testing NIM tool-calling mode config selection...")
    
    # Create a WebServer instance
    server = WebServer()
    
    # Test tool-calling mode selection
    config_path = server._resolve_config_path("nim", "tool-calling")
    expected_path = "configs/config-nim-tool-calling-conversation.yml"
    
    if expected_path in config_path:
        print(f"   ✅ Tool-calling mode: PASSED")
        print(f"      Selected: {config_path}")
        return True
    else:
        print(f"   ❌ Tool-calling mode: FAILED")
        print(f"      Expected: {expected_path}")
        print(f"      Got: {config_path}")
        return False


def test_nim_react_config_selection():
    """Test that selecting 'react' mode with 'nim' model loads the correct config."""
    print("🧪 Testing NIM react mode config selection...")
    
    # Create a WebServer instance
    server = WebServer()
    
    # Test react mode selection
    config_path = server._resolve_config_path("nim", "react")
    expected_path = "configs/config-nim-react-fixed.yml"
    
    if expected_path in config_path:
        print(f"   ✅ React mode: PASSED")
        print(f"      Selected: {config_path}")
        return True
    else:
        print(f"   ❌ React mode: FAILED")
        print(f"      Expected: {expected_path}")
        print(f"      Got: {config_path}")
        return False


def test_nim_auto_mode_default():
    """Test that 'auto' mode with 'nim' model defaults to tool-calling config."""
    print("🧪 Testing NIM auto mode default selection...")
    
    # Create a WebServer instance
    server = WebServer()
    
    # Test auto mode selection
    config_path = server._resolve_config_path("nim", "auto")
    expected_path = "configs/config-nim-tool-calling-conversation.yml"
    
    if expected_path in config_path:
        print(f"   ✅ Auto mode default: PASSED")
        print(f"      Selected: {config_path}")
        return True
    else:
        print(f"   ❌ Auto mode default: FAILED")
        print(f"      Expected: {expected_path}")
        print(f"      Got: {config_path}")
        return False


def test_explicit_mode_choice_respected():
    """Test that explicit mode choices are respected and not overridden."""
    print("🧪 Testing that explicit mode choices are respected...")
    
    server = WebServer()
    
    # Test various explicit combinations
    test_cases = [
        ("nim", "tool-calling", "config-nim-tool-calling-conversation.yml"),
        ("nim", "react", "config-nim-react-fixed.yml"),
        ("ollama", "tool-calling", "config-ollama-tool-calling.yml"),
        ("ollama", "react", "config-ollama-react-enhanced.yml"),
    ]
    
    all_passed = True
    
    for model, mode, expected_config in test_cases:
        config_path = server._resolve_config_path(model, mode)
        
        if expected_config in config_path or config_path.endswith(expected_config):
            print(f"   ✅ {model} + {mode}: PASSED")
        else:
            print(f"   ❌ {model} + {mode}: FAILED")
            print(f"      Expected: {expected_config}")
            print(f"      Got: {config_path}")
            all_passed = False
    
    return all_passed


def test_case_insensitive_model_mode():
    """Test that model and mode parameters are case-insensitive."""
    print("🧪 Testing case-insensitive model/mode handling...")
    
    server = WebServer()
    
    # Test case variations
    test_cases = [
        ("NIM", "TOOL-CALLING", "config-nim-tool-calling-conversation.yml"),
        ("nim", "Tool-Calling", "config-nim-tool-calling-conversation.yml"),
        ("NIM", "react", "config-nim-react-fixed.yml"),
        ("nim", "REACT", "config-nim-react-fixed.yml"),
    ]
    
    all_passed = True
    
    for model, mode, expected_config in test_cases:
        config_path = server._resolve_config_path(model, mode)
        
        if expected_config in config_path:
            print(f"   ✅ {model} + {mode}: PASSED")
        else:
            print(f"   ❌ {model} + {mode}: FAILED")
            print(f"      Expected: {expected_config}")
            print(f"      Got: {config_path}")
            all_passed = False
    
    return all_passed


def test_config_files_exist():
    """Test that the expected configuration files actually exist."""
    print("🧪 Testing that configuration files exist...")
    
    base_dir = Path("configs")
    expected_configs = [
        "config-nim-tool-calling-conversation.yml",
        "config-nim-react-fixed.yml",
        "config-ollama-tool-calling.yml", 
        "config-ollama-react-enhanced.yml",
    ]
    
    all_exist = True
    
    for config_file in expected_configs:
        config_path = base_dir / config_file
        if config_path.exists():
            print(f"   ✅ {config_file}: EXISTS")
        else:
            print(f"   ❌ {config_file}: MISSING")
            all_exist = False
    
    return all_exist


def main():
    """Run all configuration selection tests."""
    print("🚀 Configuration Selection Test Suite")
    print("This test verifies that mode selection correctly loads the appropriate config files.")
    print("=" * 70)
    
    success = True
    
    # Test individual mode selections
    success &= test_nim_tool_calling_config_selection()
    success &= test_nim_react_config_selection() 
    success &= test_nim_auto_mode_default()
    
    print()
    
    # Test comprehensive mode choice respect
    success &= test_explicit_mode_choice_respected()
    
    print()
    
    # Test case insensitivity
    success &= test_case_insensitive_model_mode()
    
    print()
    
    # Test config file existence
    success &= test_config_files_exist()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Mode selection is working correctly.")
        print("✅ Tool-calling mode loads config-nim-tool-calling-conversation.yml")
        print("✅ React mode loads config-nim-react-fixed.yml") 
        print("✅ Explicit user choices are respected.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("⚠️  There may be issues with mode selection logic.")
    
    return success


if __name__ == "__main__":
    # Run the test
    success = main()
    sys.exit(0 if success else 1)
