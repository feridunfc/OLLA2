# tests/conftest.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
print("✅ Added project root to sys.path:", sys.path[0])
