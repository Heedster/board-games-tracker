#!/bin/bash

# Create a deployment directory
mkdir -p deployment

# Copy the Python files
cp app.py deployment/
cp requirements.txt deployment/

# Install dependencies
cd deployment
pip install -r requirements.txt --target .

# Create a zip file
zip -r ../deployment.zip .

# Clean up
cd ..
rm -rf deployment 