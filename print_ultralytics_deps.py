import sys

# Track modules before import
before = set(sys.modules.keys())

try:
    import ultralytics
    print("ultralytics imported successfully.")
except Exception as e:
    print(f"Failed to import ultralytics: {e}")
    sys.exit(1)

# Track modules after import
after = set(sys.modules.keys())
imported = after - before

excluded_candidates = ["scipy", "pandas", "matplotlib", "h5py", "sympy", "IPython", "notebook", "jinja2", "sklearn", "scikit-learn", "tensorflow", "tensorboard", "keras", "PyQt5", "PySide2", "PySide6", "boto3", "botocore", "cryptography", "sqlalchemy"]

print("\nImported modules that were in our excludes list:")
for m in excluded_candidates:
    # Check if this module name or any submodule of it was loaded
    loaded_submodules = [name for name in imported if name == m or name.startswith(m + ".")]
    if loaded_submodules:
        print(f" - {m} (loaded as {loaded_submodules[:3]}...)")
