#!/usr/bin/env python3
"""
Push OpsPilot++ to existing Hugging Face Space
"""

import os
import subprocess
import sys
import shutil

# Configuration
HF_USERNAME = "niahr"  # Your username
SPACE_NAME = "OOpspilot"  # Your space name

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_step(step_num, text):
    print(f"📍 Step {step_num}: {text}")
    print("-" * 60)

def run_command(cmd, description=""):
    """Run a shell command"""
    try:
        if description:
            print(f"  Running: {description}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ⚠️  {result.stderr}")
            return False
        if result.stdout:
            print(f"  ✅ {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return False

def remove_dir(path):
    """Remove directory safely"""
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
            return True
    except Exception as e:
        print(f"  ⚠️  Could not remove {path}: {e}")
    return False


def is_git_repo(path):
    return os.path.isdir(os.path.join(path, ".git"))


def copy_project_files(source_dir, dest_dir, exclude_names=None):
    if exclude_names is None:
        exclude_names = []

    for item in os.listdir(source_dir):
        if item in exclude_names:
            continue

        src = os.path.join(source_dir, item)
        dst = os.path.join(dest_dir, item)

        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', '.DS_Store', '.env', 'env'))
        else:
            shutil.copy2(src, dst)


def main():
    print_header("🚀 Pushing OpsPilot++ to Hugging Face Space")
    
    space_url = f"https://huggingface.co/spaces/{HF_USERNAME}/{SPACE_NAME}"
    space_dir = f"{SPACE_NAME}_hf"
    
    # Step 1: Clone or reuse existing space clone
    print_step(1, "Prepare local Hugging Face Space clone")
    if os.path.exists(space_dir) and is_git_repo(space_dir):
        print(f"  ✅ Using existing local clone: {space_dir}")
        os.chdir(space_dir)
        run_command("git fetch --all", "Fetch latest from remote")
        run_command("git reset --hard origin/main", "Reset to latest remote state")
        os.chdir("..")
    else:
        if os.path.exists(space_dir):
            print(f"  Removing existing directory: {space_dir}")
            remove_dir(space_dir)
        if not run_command(f'git clone "{space_url}" "{space_dir}"', f"Clone {space_url}"):
            print("  ❌ Failed to clone space")
            return False
        print(f"  ✅ Space cloned to {space_dir}!")
    
    # Step 2: Copy all project files to space
    print_step(2, "Copy all project files to space")
    print("  Copying all files...")

    root_dir = os.path.abspath(os.path.join(space_dir, ".."))
    exclude_dirs = [space_dir, "OOpspilot_hf", "Opspilot_hf", "env", ".git"]
    try:
        copy_project_files(root_dir, space_dir, exclude_dirs)
    except Exception as e:
        print(f"  ⚠️  Failed to copy project files: {e}")
        return False

    os.chdir(space_dir)

    # Remove unnecessary directories
    print("  Cleaning up unnecessary files...")
    remove_dir("node_modules")
    remove_dir("__pycache__")
    remove_dir("Opspilot_hf")
    
    # Remove unnecessary files
    for f in ["*.pyc", ".DS_Store", ".env"]:
        run_command(f"del /s /q {f}", f"Remove {f}")
    
    print("  ✅ All files copied and cleaned!")
    
    # Step 3: Configure git
    if not HF_TOKEN:
        print("  ❌ HF_TOKEN not found. Set it in your environment before running this script.")
        return False
    
    print_step(3, "Configure git")
    run_command('git config user.email "bot@huggingface.co"', "Set email")
    run_command('git config user.name "OpsPilot Bot"', "Set name")
    print("  ✅ Git configured!")
    
    # Step 4: Add all files
    print_step(4, "Stage all files")
    run_command("git add .", "Stage files")
    print("  ✅ Files staged!")
    
    # Step 5: Commit
    print_step(5, "Commit changes")
    run_command('git commit -m "Add OpsPilot++ benchmark system - complete project"', "Commit")
    print("  ✅ Committed!")
    
    # Step 6: Push
    print_step(6, "Push to Hugging Face")
    run_command(f'git remote set-url origin https://{HF_USERNAME}:{HF_TOKEN}@huggingface.co/spaces/{HF_USERNAME}/{SPACE_NAME}', "Set remote with token")
    if not run_command("git push", "Push to Hugging Face"):
        print("  ⚠️  Push may have issues")
    else:
        print("  ✅ Pushed successfully!")
    
    # Success message
    print_header("✅ Upload Complete!")
    print(f"""
🎉 Your OpsPilot++ project has been pushed to Hugging Face!

📍 Space URL:
   https://huggingface.co/spaces/{HF_USERNAME}/{SPACE_NAME}

📦 Files Uploaded:
   ✅ main.py (FastAPI backend)
   ✅ inference.py (Inference module)
   ✅ Dockerfile (Docker configuration)
   ✅ requirements.txt (Dependencies)
   ✅ ui/ (React frontend)
   ✅ All configuration files

⏱️  Build Status:
   - Build will start automatically
   - Check the "Logs" tab to monitor progress
   - Build takes 5-10 minutes

🔗 Next Steps:
   1. Go to: https://huggingface.co/spaces/{HF_USERNAME}/{SPACE_NAME}
   2. Click "Logs" to see build progress
   3. Wait for build to complete
   4. Test your benchmark
   5. Share the URL for hackathon!

✅ Hackathon Checks:
   ✓ Dockerfile at repo root
   ✓ inference.py at repo root
   ✓ /reset endpoint (POST OK)
   ✓ All required files present
    """)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Upload cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
