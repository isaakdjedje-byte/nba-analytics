# Python Version Fix for NBA-14

## Problem
Python 3.14.2 is incompatible with PySpark 3.5.0's bundled cloudpickle.
This causes RecursionError when Spark tries to serialize functions.

## Solution

### Option 1: Use pyenv (Recommended)

```bash
# Install Python 3.11.9
pyenv install 3.11.9

# Set local version for this project
pyenv local 3.11.9

# Verify
python --version  # Should show 3.11.9

# Reinstall dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/test_schema_evolution.py -v
```

### Option 2: Use virtualenv with specific Python

```bash
# If you have Python 3.11 installed elsewhere
virtualenv -p /path/to/python3.11 venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m pytest tests/test_schema_evolution.py -v
```

### Option 3: Update PySpark (Alternative)

```bash
# Try latest PySpark version
pip install pyspark==3.5.3

# If that doesn't work, downgrade Python
```

## Verification

After switching to Python 3.11, run:
```bash
python -c "import pyspark; print(pyspark.__version__)"
python -m pytest tests/test_schema_evolution.py::TestMergeSchema::test_merge_schema_basic -v
```

The test should pass without RecursionError.

## Why This Happens

- Python 3.14 introduced internal changes to code objects
- PySpark 3.5.0 bundles cloudpickle from 2023
- cloudpickle's function serialization is incompatible with Python 3.14
- This causes infinite recursion when serializing any function

## References

- PySpark compatibility: https://spark.apache.org/docs/latest/api/python/getting_started/install.html
- cloudpickle issues: https://github.com/cloudpipe/cloudpickle/issues
