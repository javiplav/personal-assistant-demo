#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Standalone test for configuration path resolution logic.
This test verifies that mode selection correctly loads the appropriate configuration files
without requiring the full web server dependencies.
"""

from pathlib import Path


def _resolve_config_path(model: str, mode: str) -> str:
    """
    Extracted config path resolution logic from WebServer._resolve_config_path
    Map model/mode selections to config file paths.
    """
    base_dir = Path("configs")
    # Normalize
    model = (model or "ollama").lower()
    mode = (mode or "react").lower()

    if model == "nim":
        if mode == "tool-calling":
            return str(base_dir / "config-nim-tool-calling-conversation.yml")
        elif mode == "react":
            return str(base_dir / "config-nim-react-fixed.yml")
        else:  # auto
            # keep your auto logic, but do NOT override an explicit user choice
            return str(base_dir / "config-nim-tool-calling-conversation.yml")
    else:  # ollama
        if mode == "tool-calling":
            candidates = [
                base_dir / "config-ollama-tool-calling.yml",
                base_dir / "config-ollama.yml",
            ]
        else:
            candidates = [
                base_dir / "config-ollama-react-enhanced.yml",
                base_dir / "config-ollama.yml",
            ]

        for path in candidates:
            if path.exists():
                return str(path)
        # Final fallback
        return str(base_dir / "config-ollama.yml")


def test_nim_tool_calling_config():
    """Test that NIM + tool-calling mode selects the correct config."""
    print("🧪 Testing NIM tool-calling mode...")
    
    config_path = _resolve_config_path("nim", "tool-calling")
    expected = "config-nim-tool-calling-conversation.yml"
    
    if expected in config_path:
        print(f"   ✅ PASSED: {config_path}")
        return True
    else:
        print(f"   ❌ FAILED: Expected {expected}, got {config_path}")
        return False


def test_nim_react_config():
    """Test that NIM + react mode selects the correct config."""
    print("🧪 Testing NIM react mode...")
    
    config_path = _resolve_config_path("nim", "react")
    expected = "config-nim-react-fixed.yml"
    
    if expected in config_path:
        print(f"   ✅ PASSED: {config_path}")
        return True
    else:
        print(f"   ❌ FAILED: Expected {expected}, got {config_path}")
        return False


def test_nim_auto_mode():
    """Test that NIM + auto mode defaults to tool-calling."""
    print("🧪 Testing NIM auto mode...")
    
    config_path = _resolve_config_path("nim", "auto")
    expected = "config-nim-tool-calling-conversation.yml"
    
    if expected in config_path:
        print(f"   ✅ PASSED: {config_path}")
        return True
    else:
        print(f"   ❌ FAILED: Expected {expected}, got {config_path}")
        return False


def test_explicit_choices_respected():
    """Test that explicit mode choices are always respected."""
    print("🧪 Testing explicit mode choices...")
    
    test_cases = [
        # (model, mode, expected_config_name)
        ("nim", "tool-calling", "config-nim-tool-calling-conversation.yml"),
        ("nim", "react", "config-nim-react-fixed.yml"),
        ("NIM", "TOOL-CALLING", "config-nim-tool-calling-conversation.yml"),  # Case insensitive
        ("nim", "React", "config-nim-react-fixed.yml"),  # Case insensitive
    ]
    
    all_passed = True
    
    for model, mode, expected in test_cases:
        config_path = _resolve_config_path(model, mode)
        if expected in config_path:
            print(f"   ✅ {model} + {mode}: PASSED")
        else:
            print(f"   ❌ {model} + {mode}: FAILED (got {config_path})")
            all_passed = False
    
    return all_passed


def test_mode_not_overridden():
    """Test that explicit mode choices are not overridden by heuristics."""
    print("🧪 Testing that explicit modes are not overridden...")
    
    # These should return exactly what we ask for, not be overridden
    explicit_tests = [
        ("nim", "tool-calling"),
        ("nim", "react"),
    ]
    
    all_passed = True
    
    for model, mode in explicit_tests:
        config_path = _resolve_config_path(model, mode)
        
        # Verify the config name matches the requested mode
        if mode == "tool-calling" and "tool-calling" in config_path:
            print(f"   ✅ {model} + {mode}: Not overridden")
        elif mode == "react" and "react" in config_path:
            print(f"   ✅ {model} + {mode}: Not overridden")
        else:
            print(f"   ❌ {model} + {mode}: Appears to be overridden! Got {config_path}")
            all_passed = False
    
    return all_passed


def test_config_files_exist():
    """Test that the expected configuration files exist."""
    print("🧪 Testing that config files exist...")
    
    expected_configs = [
        "configs/config-nim-tool-calling-conversation.yml",
        "configs/config-nim-react-fixed.yml",
    ]
    
    all_exist = True
    
    for config_path in expected_configs:
        path = Path(config_path)
        if path.exists():
            print(f"   ✅ {config_path}: EXISTS")
        else:
            print(f"   ❌ {config_path}: MISSING")
            all_exist = False
    
    return all_exist


def main():
    """Run all configuration selection tests."""
    print("🚀 Configuration Path Resolution Test")
    print("This test verifies mode selection logic loads correct config files.")
    print("=" * 60)
    
    success = True
    
    # Core functionality tests
    success &= test_nim_tool_calling_config()
    success &= test_nim_react_config()
    success &= test_nim_auto_mode()
    
    print()
    
    # Test explicit choice handling
    success &= test_explicit_choices_respected()
    success &= test_mode_not_overridden()
    
    print()
    
    # Test file existence
    success &= test_config_files_exist()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ tool-calling mode → config-nim-tool-calling-conversation.yml")
        print("✅ react mode → config-nim-react-fixed.yml")
        print("✅ Explicit user choices are respected (not overridden)")
        print("✅ Case-insensitive mode handling works correctly")
    else:
        print("❌ SOME TESTS FAILED!")
        print("⚠️  There may be issues with config path resolution.")
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
