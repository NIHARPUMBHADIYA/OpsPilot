#!/bin/bash

# OpsPilot++ Deployment Script for Hugging Face Spaces

# Set your credentials
HF_TOKEN="${HF_TOKEN:-${HUGGINGFACE_TOKEN:-}}"
HF_USERNAME="niahr"  # ⚠️ IMPORTANT: Replace 'your-username' with your actual Hugging Face username
SPACE_NAME="opspilot-benchmark"

echo "🚀 Deploying OpsPilot++ to Hugging Face Spaces..."
echo ""

if [ -z "$HF_TOKEN" ]; then
    echo "❌ Set HF_TOKEN or HUGGINGFACE_TOKEN before running this script."
    exit 1
fi

# Step 1: Login to Hugging Face
echo "📝 Step 1: Logging in to Hugging Face..."
python -m huggingface_hub.cli login --token $HF_TOKEN
echo "✅ Logged in successfully!"
echo ""

# Step 2: Create Space (if it doesn't exist)
echo "📦 Step 2: Creating Hugging Face Space..."
python -m huggingface_hub.cli repo create $SPACE_NAME --repo_type space --space_sdk docker --private false 2>/dev/null || echo "Space already exists or error occurred"
echo ""

# Step 3: Clone the space
echo "📥 Step 3: Cloning space repository..."
if [ -d "$SPACE_NAME" ]; then
    rm -rf $SPACE_NAME
fi
git clone https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME
cd $SPACE_NAME
echo "✅ Space cloned!"
echo ""

# Step 4: Copy all project files
echo "📋 Step 4: Copying project files..."
cp -r ../* . 2>/dev/null || true
cp -r ../.[^.]* . 2>/dev/null || true
echo "✅ Files copied!"
echo ""

# Step 5: Configure git
echo "🔧 Step 5: Configuring git..."
git config user.email "bot@huggingface.co"
git config user.name "OpsPilot Bot"
echo ""

# Step 6: Add and commit
echo "📤 Step 6: Committing files..."
git add .
git commit -m "Deploy OpsPilot++ benchmark system" || echo "Nothing to commit"
echo ""

# Step 7: Push to Hugging Face
echo "🚀 Step 7: Pushing to Hugging Face Spaces..."
git push
echo ""

echo "✅ Deployment complete!"
echo ""
echo "🎉 Your space is now available at:"
echo "https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME"
echo ""
echo "⏱️  Build will take 5-10 minutes. Check the Logs tab to monitor progress."
