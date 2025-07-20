#!/bin/bash
# Wrapper script to run GitLab test with environment variables

# Load environment variables
source .env

# Change to src directory
cd src

# Run the test
python ../scripts/testing/test_complete_gitlab_setup.py