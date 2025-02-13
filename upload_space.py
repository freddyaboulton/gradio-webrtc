import argparse
import os
from pathlib import Path
import yaml
from dotenv import load_dotenv
from huggingface_hub import HfApi
from huggingface_hub.hf_api import SpaceHardware  # type: ignore


def parse_readme_secrets(readme_path: Path) -> list[str]:
    """Extract secret names from README.md tags field."""
    if not readme_path.exists():
        return []

    content = readme_path.read_text()
    try:
        # Parse the YAML frontmatter
        # Find the content between first two '---' lines
        yaml_content = content.split("---")[1]
        metadata = yaml.safe_load(yaml_content)

        # Extract secrets from tags
        secrets = []
        if "tags" in metadata:
            for tag in metadata["tags"]:
                if "|" in tag:
                    prefix, secret_name = tag.split("|")
                    if prefix == "secret":
                        secrets.append(secret_name)
        return secrets
    except Exception as e:
        print(f"Warning: Could not parse README.md: {e}")
        return []


def upload_space(dir_path: str):
    path: Path = Path(dir_path)
    if not path.exists():
        raise ValueError(f"Path {path} does not exist")

    # Get space name from last directory name
    space_name = path.name.replace("_", "-")

    # Load environment variables
    env_file = path.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        print("Warning: No .env file found")

    # Initialize Hugging Face client
    api = HfApi()

    # Create full repo ID
    repo_id = f"fastrtc/{space_name}"
    print(f"Creating/updating space: {repo_id}")

    # Create the space if it doesn't exist
    try:
        api.create_repo(
            repo_id=repo_id, repo_type="space", space_sdk="gradio", exist_ok=True
        )
    except Exception as e:
        print(f"Error creating repo: {e}")
        return

    # Upload all files from the directory
    print("Uploading files...")
    api.upload_folder(
        repo_id=repo_id,
        repo_type="space",
        folder_path=str(path),
        ignore_patterns=["__pycache__", "*.pyc", ".env"],
        create_pr=False,
        path_in_repo="",
    )

    # if api.space_info(repo_id=repo_id).runtime.hardware != SpaceHardware.CPU_UPGRADE:  # type: ignore
    #     api.request_space_hardware(repo_id=repo_id, hardware="cpu-upgrade")  # type: ignore

    # Handle secrets
    readme_path = path / "README.md"
    secret_names = parse_readme_secrets(readme_path)

    if secret_names:
        print("Setting up secrets...")
        for secret_name in secret_names:
            secret_value = os.getenv(secret_name)
            if secret_value:
                try:
                    api.add_space_secret(
                        repo_id=repo_id, key=secret_name, value=secret_value
                    )
                    print(f"Added secret: {secret_name}")
                except Exception as e:
                    print(f"Error adding secret {secret_name}: {e}")
            else:
                print(
                    f"Warning: Secret {secret_name} not found in environment variables"
                )

    print(
        f"\nSpace uploaded successfully! View it at: https://huggingface.co/spaces/{repo_id}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Upload a directory as a Hugging Face Space"
    )
    parser.add_argument("path", help="Path to the directory to upload")

    args = parser.parse_args()
    upload_space(args.path)


if __name__ == "__main__":
    main()
