
---

### `setup.sh`

```bash
#!/bin/bash

echo "Setting up Maya Asset Import Tool environment..."

# 1. Create virtual environment if it doesn't exist
if [ ! -d "venv39" ]; then
    echo "Creating Python 3.9 virtual environment 'venv39'..."
    python3.9 -m venv venv39
fi

# 2. Activate the virtual environment
source venv39/bin/activate

# 3. Upgrade pip and install dependencies
echo "Installing Python dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Set PYTHONPATH to include project source folders
export PYTHONPATH=$PYTHONPATH:$(pwd)/src:$(pwd)/ui
echo "PYTHONPATH set to: $PYTHONPATH"

# 5. Maya plugin reminder
echo "Make sure the 'mayaUsdPlugin' is enabled in Maya."

# 6. Instructions to launch the tool in Maya
echo ""
echo "To launch the Asset Import Tool in Maya, open the Script Editor (Python tab) and run:"
echo ""
echo "    exec(open('$(pwd)/install_shelf_button.py').read())"
echo ""
echo "This will add a shelf button in Maya to launch the tool."

# 7. Optional: Copy test assets (uncomment to use)
# mkdir -p test_assets
# cp -r initial_assets/* test_assets/
# echo "Test assets copied to test_assets/"

echo ""
echo "Setup complete. You can now launch Maya and use the tool."
```

---

### How to Use (Terminal)

1. Give the script permission to run (only needed once):

```bash
chmod +x setup.sh
```

2. Run the setup script:

```bash
./setup.sh
```

---

### Post-Setup: Launching the Tool in Maya

After running the script:

1. Open Maya.
2. Go to **Script Editor → Python** tab.
3. Paste and run the following command (update the path if necessary):

```python
exec(open('/your/full/path/to/install_shelf_button.py').read())
```

This will create a shelf button in Maya. Click the button to launch the Asset Import & Preparation Tool.

---
