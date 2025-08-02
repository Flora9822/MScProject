#!/bin/bash

echo "Setting up project environment..."

# 1. Create and activate venv (optional)
python3.9 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment variables (example)
export PYTHONPATH=$PYTHONPATH:/path/to/your/project/src:/path/to/your/project/ui

# 4. Enable Maya plugin (example)
# Might require launching maya or using maya batch commands
echo "Please enable mayaUsdPlugin in Maya before running the tool."

# 5. Copy rules or assets if needed
mkdir -p test_assets
cp -r initial_assets/* test_assets/

echo "Setup complete. You can now launch Maya and run the tool."
