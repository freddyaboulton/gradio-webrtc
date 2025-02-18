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
    uvicorn demo.{{name}}.app:app --port 8000

# Run the gradio ui for a demo
gradio name:
    python demo/{{name}}/app.py

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


# Build the package
build:
    gradio cc build --no-generate-docs

# Format the code
format:
    ruff format .
    ruff check --fix .
    ruff check --select I --fix .
