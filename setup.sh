#!/bin/bash

# Step 1: Create venv
echo "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo "Virtual environment created."
fi

# Step 2:
echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate

# Install the required dependencies from requirements.txt
pip install -r requirements.txt

# Step 3: Create Zip files
echo "Creating Lambda ZIP files..."
python3 bundle_lambdas.py

# Step 4: Backend Deploy
echo "Deploying the backend..."
python3 deploy_backend.py

echo "Deployment completed successfully."

