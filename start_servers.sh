#!/bin/bash

# Create fresh virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Note: .env will be sourced automatically
overmind start
