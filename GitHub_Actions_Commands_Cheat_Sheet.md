# -------------------------------
# TERMINAL COMMANDS
# -------------------------------

# Print a message
echo "Hello GitHub Actions"

# Display current directory
pwd

# List files and directories
ls

# Create a directory
mkdir folder_name

# Change directory
cd folder_name

# Check Python version
python --version

# Upgrade pip
python -m pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Run all pytest test cases
pytest

# Run pytest with detailed output
pytest -v

# Collect tests without executing them
pytest --collect-only

# Run smoke tests
pytest -m smoke

# Run regression tests
pytest -m regression

# Generate HTML test report
pytest -v --html=report.html --self-contained-html


# -------------------------------
# GITHUB ACTIONS YAML SYNTAX
# -------------------------------

name: Running all tests

on:
  push:
    branches:
      - main
    paths:
      - 'tests/**'

  pull_request:
    types:
      - opened
      - synchronize
      - reopened

  workflow_dispatch:

jobs:
  all_tests:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run all tests
        run: pytest -v

      - name: Upload HTML Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: pytest-html-report
          path: report.html
          retention-days: 7
          if-no-files-found: warn


# -------------------------------
# ENVIRONMENT VARIABLES & SECRETS
# -------------------------------

# Define environment variables
env:
  BASE_URL: https://example.com
  BOOKER_USERNAME: ${{ secrets.BOOKER_USERNAME }}
  BOOKER_PASSWORD: ${{ secrets.BOOKER_PASSWORD }}

# Read environment variables in Python
import os

base_url = os.getenv("BASE_URL")
username = os.getenv("BOOKER_USERNAME")
password = os.getenv("BOOKER_PASSWORD")


# -------------------------------
# USEFUL GITHUB ACTIONS CONDITIONS
# -------------------------------

# Always execute the step
if: always()

# Execute only when the previous steps succeed
if: success()

# Execute only when a previous step fails
if: failure()


# -------------------------------
# IMPORTANT GITHUB ACTIONS KEYS
# -------------------------------

name:          # Workflow name
on:            # Workflow triggers
push:          # Push event
pull_request:  # Pull request event
workflow_dispatch: # Manual trigger
schedule:      # Scheduled trigger
branches:      # Branch filter
paths:         # File path filter
types:          # Event type filter
jobs:          # Jobs in workflow
runs-on:       # Runner environment
steps:         # Steps inside a job
uses:          # Use an existing action
run:           # Execute shell commands
with:          # Action configuration
env:           # Environment variables
timeout-minutes: # Job timeout