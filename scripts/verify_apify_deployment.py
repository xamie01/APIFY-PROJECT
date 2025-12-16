#!/usr/bin/env python3
"""
Verify Apify actor deployment readiness.

This script checks that all required files and configurations are in place
for successful deployment to the Apify platform.

Based on: https://docs.apify.com/academy/deploying-your-code/python-actors
"""

import json
import os
import re
import sys
from pathlib import Path


def check_file_exists(path, description):
    """Check if a file exists."""
    if os.path.exists(path):
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ MISSING {description}: {path}")
        return False


def verify_json_valid(path, description):
    """Verify a JSON file is valid."""
    try:
        with open(path) as f:
            data = json.load(f)
        print(f"✅ {description} is valid JSON")
        return True, data
    except Exception as e:
        print(f"❌ {description} is invalid: {e}")
        return False, None


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("Apify Actor Deployment Verification")
    print("=" * 70)
    
    checks_passed = 0
    checks_total = 0
    
    # Required files according to Apify Python Actor docs
    print("\n📋 Checking Required Files...")
    
    # 1. Check .actor/actor.json
    checks_total += 1
    if check_file_exists(".actor/actor.json", "Actor configuration"):
        valid, config = verify_json_valid(".actor/actor.json", "actor.json")
        if valid:
            checks_passed += 1
            print(f"   - Name: {config.get('name', 'N/A')}")
            print(f"   - Version: {config.get('version', 'N/A')}")
            print(f"   - Dockerfile: {config.get('dockerfile', 'N/A')}")
    
    # 2. Check .actor/INPUT_SCHEMA.json
    checks_total += 1
    if check_file_exists(".actor/INPUT_SCHEMA.json", "Input schema"):
        valid, schema = verify_json_valid(".actor/INPUT_SCHEMA.json", "INPUT_SCHEMA.json")
        if valid:
            checks_passed += 1
            props = schema.get('properties', {})
            print(f"   - Input parameters: {len(props)}")
            print(f"   - Parameters: {', '.join(props.keys())}")
    
    # 3. Check src/__main__.py
    checks_total += 1
    if check_file_exists("src/__main__.py", "Actor entry point"):
        try:
            # Verify the file exists and contains the expected imports
            with open("src/__main__.py") as f:
                content = f.read()
                # Check for required imports
                if 'from src.main import main' in content and 'asyncio.run(main())' in content:
                    print("   - Contains correct entry point code")
                    checks_passed += 1
                else:
                    print("   - ⚠️  May be missing required imports")
        except Exception as e:
            print(f"   - Read failed: {e}")
    
    # 4. Check Dockerfile
    checks_total += 1
    if check_file_exists("Dockerfile", "Docker configuration"):
        with open("Dockerfile") as f:
            dockerfile_content = f.read()
            # Check for python -m src entry point with flexible regex
            entry_point_pattern = r'CMD\s*\[.*["\']python["\'].*["\'](?:-m\s+)?src["\'].*\]|python\s+-m\s+src'
            if re.search(entry_point_pattern, dockerfile_content):
                print("   - Correct entry point: python -m src")
                checks_passed += 1
            else:
                print("   - ⚠️  Entry point may be incorrect")
    
    # 5. Check requirements.txt
    checks_total += 1
    if check_file_exists("requirements.txt", "Python dependencies"):
        with open("requirements.txt") as f:
            deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            print(f"   - Dependencies: {len(deps)}")
            # Check for apify SDK
            if any('apify' in dep.lower() for dep in deps):
                print("   - Apify SDK included")
                checks_passed += 1
            else:
                print("   - ⚠️  Apify SDK may be missing")
    
    # Optional but recommended files
    print("\n📄 Checking Optional Files...")
    
    optional_files = {
        "README.md": "Project documentation",
        ".dockerignore": "Docker build optimization",
        ".actor/README.md": "Actor configuration guide",
        ".actor/INPUT_EXAMPLE.json": "Example input",
    }
    
    for file_path, description in optional_files.items():
        if check_file_exists(file_path, description):
            pass
        else:
            print(f"⚠️  Optional: {description}")
    
    # Check prompts directory
    print("\n📁 Checking Project Structure...")
    if os.path.exists("prompts"):
        prompt_files = list(Path("prompts").rglob("*.json"))
        print(f"✅ Prompts directory: {len(prompt_files)} prompt files found")
    else:
        print("❌ Prompts directory not found")
    
    # Summary
    print("\n" + "=" * 70)
    print(f"Verification Results: {checks_passed}/{checks_total} required checks passed")
    print("=" * 70)
    
    if checks_passed == checks_total:
        print("\n🎉 SUCCESS! All Apify deployment requirements are met.")
        print("\nYou can now deploy with:")
        print("  1. apify login")
        print("  2. apify push")
        return 0
    else:
        print(f"\n⚠️  {checks_total - checks_passed} check(s) failed. Please fix the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
