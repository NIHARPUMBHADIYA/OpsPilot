#!/usr/bin/env python3
"""
OpsPilot++ Hugging Face Deployment Script
Run this script to deploy to Hugging Face Spaces
"""

import os
import subprocess
import sys
from huggingface_hub import login, whoami
from huggingface_hub.commands.repo import repo_create

# Configuration
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN") or ""
SPACE_NAME = "opspilot"

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_step(step_num, text):
    print(f"📍 Step {step_num}: {text}")
    print("-" * 60)

def run_command(cmd, description=""):
    """Run a shell command and return success status"""
    try:
        if description:
            print(f"  Running: {description}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ❌ Error: {result.stderr}")
            return False
        if result.stdout:
            print(f"  {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return False

def main():
    print_header("🚀 OpsPilot++ Hugging Face Deployment")
    
    # Step 1: Login
    print_step(1, "Login to Hugging Face")
    if not HF_TOKEN:
        print("  ❌ Set HF_TOKEN or HUGGINGFACE_TOKEN before running this script.")
        return False
    try:
        login(token=HF_TOKEN)
        print("  ✅ Logged in successfully!")
    except Exception as e:
        print(f"  ❌ Login failed: {e}")
        return False
    
    # Step 2: Get username
    print_step(2, "Get your Hugging Face username")
    try:
        user_info = whoami()
        username = user_info.get("name") or user_info.get("username")
        print(f"  ✅ Username: {username}")
    except Exception as e:
        print(f"  ❌ Failed to get username: {e}")
        return False
    
    # Step 3: Create space
    print_step(3, "Create Hugging Face Space")
    try:
        repo_create(
            repo_id=SPACE_NAME,
            repo_type="space",
            space_sdk="docker",
            private=False,
            exist_ok=True
        )
        print(f"  ✅ Space created/verified: {SPACE_NAME}")
    except Exception as e:
        print(f"  ⚠️  Space creation note: {e}")
    
    # Step 4: Clone space
    print_step(4, "Clone space repository")
    space_url = f"https://huggingface.co/spaces/{username}/{SPACE_NAME}"
    if os.path.exists(SPACE_NAME):
        print(f"  Removing existing directory: {SPACE_NAME}")
        run_command(f"rmdir /s /q {SPACE_NAME}", "Remove old directory")
    
    if not run_command(f'git clone "{space_url}"', f"Clone {space_url}"):
        print("  ❌ Failed to clone space")
        return False
    print(f"  ✅ Space cloned!")
    
    # Step 5: Copy files
    print_step(5, "Copy project files to space")
    os.chdir(SPACE_NAME)
    
    # Copy all files from parent directory
    print("  Copying files...")
    run_command("xcopy ..\\* . /E /I /Y /EXCLUDE:..\\exclude.txt", "Copy files")
    print("  ✅ Files copied!")
    
    # Step 6: Configure git
    print_step(6, "Configure git")
    run_command('git config user.email "bot@huggingface.co"', "Set email")
    run_command('git config user.name "OpsPilot Bot"', "Set name")
    print("  ✅ Git configured!")
    
    # Step 7: Commit and push
    print_step(7, "Commit and push to Hugging Face")
    run_command("git add .", "Stage files")
    run_command('git commit -m "Deploy OpsPilot++ benchmark system"', "Commit")
    
    if not run_command("git push", "Push to Hugging Face"):
        print("  ⚠️  Push may have failed, check manually")
    else:
        print("  ✅ Pushed successfully!")
    
    # Success message
    print_header("✅ Deployment Complete!")
    print(f"""
🎉 Your OpsPilot++ space is being deployed!

📍 Space URL:
   https://huggingface.co/spaces/{username}/{SPACE_NAME}

⏱️  Build Status:
   - Build will take 5-10 minutes
   - Check the "Logs" tab to monitor progress
   - Once complete, your space will be live!

📝 For Hackathon Submission:
   Project: OpsPilot++
   Hugging Face Space: https://huggingface.co/spaces/{username}/{SPACE_NAME}
   Description: Production-grade AI operations benchmark

🔗 Next Steps:
   1. Go to your space URL above
   2. Click "Logs" to monitor the build
   3. Wait for build to complete
   4. Test your benchmark
   5. Share the URL for hackathon submission!
    """)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
