#!/bin/bash
set -e  # Hata olduğunda çık

# Detect if running in GitHub Actions
if [ "$GITHUB_ACTIONS" = "true" ]; then
  echo "Running inside GitHub Actions CI environment..."
  echo "Installing dependencies..."
  pip install -r requirements.txt
else
  echo "🧩 Running locally..."
  # Step 1: Create venv (only locally)
  if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
  fi

  # Step 2: Activate venv
  echo "Activating virtual environment and installing dependencies..."
  source venv/bin/activate
  pip install -r requirements.txt
fi

# Step 3: Bundle Lambda ZIPs
echo "Creating Lambda ZIP files..."
python3 bundle_lambdas.py

# Step 4: Deploy backend
echo "Deploying the backend..."
python3 deploy_backend.py

echo "Deployment completed successfully."

