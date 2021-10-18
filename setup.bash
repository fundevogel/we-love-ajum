#!/bin/bash

# Set up & activate virtualenv
virtualenv -p python3 venv

# shellcheck disable=SC1091
source venv/bin/activate

# Install dependencies
python -m pip install --editable .
