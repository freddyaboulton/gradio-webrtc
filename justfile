# Upload a single demo space
default:
    @just --list

upload path:
    python upload_space.py demo/{{path}}

# Upload all demo spaces
upload-all:
    python upload_space.py demo --all

# Run a demo with uvicorn
run name:
    uvicorn demo.{{name}}.app:stream --host 0.0.0.0 --port 7860

# Run a demo with phone mode
phone name:
    PHONE=1 python demo/{{name}}/app.py

# Upload the latest wheel file to PyPI using twine
publish:
    #!/usr/bin/env python
    import glob
    import os
    from pathlib import Path
    
    # Find all wheel files in dist directory
    wheels = glob.glob('dist/*.whl')
    if not wheels:
        print("No wheel files found in dist directory")
        exit(1)
    
    # Sort by creation time to get the latest
    latest_wheel = max(wheels, key=os.path.getctime)
    print(f"Uploading {latest_wheel}")
    os.system(f"twine upload {latest_wheel}")
