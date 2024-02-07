import os
import subprocess
import httpx
import dotenv
from packaging import version
from fastapi import APIRouter, BackgroundTasks, Body
from pydantic import BaseModel

dotenv.load_dotenv()

router = APIRouter()

CURRENT_LEISAIR_ML_VERSION = os.getenv("LEISAIR_ML_VERSION", "unknown")

async def get_latest_version(package_name: str) -> str:
    """
    Fetch the latest semantic version tag of a package from GitHub Container Registry.
    """
    url = f"https://ghcr.io/v2/{os.getenv('GITHUB_USERNAME')}/{package_name}/tags/list"
    headers = {
        "Authorization": f"Bearer {os.getenv('ENCODED_GITHUB_TOKEN')}"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        print("RESPONSE: ", response.text)
        if response.is_error:
            return "unknown"  # or handle the error as needed

        data = response.json()
        tags = data.get("tags", [])
        print("TAGS: ", tags)

        if not tags:
            return "unknown"

        # Filter out non-semantic version tags and sort them
        semantic_tags = []
        for tag in tags:
            try:
                # This will raise an exception if tag is not a valid semantic version
                parsed_version = version.parse(tag)
                if not parsed_version.is_prerelease and not parsed_version.is_devrelease:
                    semantic_tags.append(tag)
            except Exception as e:
                print(f"Skipping non-semantic version tag: {tag} - {e}")

        if not semantic_tags:
            return "unknown"

        # Sort the versions using packaging.version.parse to ensure semantic versioning order
        latest_version_tag = sorted(semantic_tags, key=lambda x: version.parse(x), reverse=True)[0]

        return latest_version_tag


@router.post("/check-updates")
async def check_updates(current_nextjs_version: str = Body(..., embed=True, title="Current leisair-nextjs version")):
    updates_info = {}

    # Check update for leisair-nextjs
    latest_nextjs_version = await get_latest_version("leisair-nextjs")
    updates_info["leisair-nextjs"] = {
        "current_version": current_nextjs_version,
        "latest_version": latest_nextjs_version,
        "update_available": current_nextjs_version != latest_nextjs_version
    }

    # Check update for leisair-ml
    latest_ml_version = await get_latest_version("leisair-ml")
    updates_info["leisair-ml"] = {
        "current_version": CURRENT_LEISAIR_ML_VERSION,
        "latest_version": latest_ml_version,
        "update_available": CURRENT_LEISAIR_ML_VERSION != latest_ml_version
    }

    return updates_info

def docker_login(username: str, token: str):
    """
    Log in to the GitHub Container Registry using the Docker CLI.
    """
    login_command = [
        "docker", "login", "ghcr.io",
        "--username", username,
        "--password-stdin"
    ]
    result = subprocess.run(login_command, input=token.encode(), capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to log in to GHCR: {result.stderr}")

def initiate_update_process(services: dict):
    """
    Initiates the update process for given services with their new tags.
    Includes a Docker login to GHCR using environment variables.

    Args:
    services (dict): A dictionary of service names and their corresponding new image tags.
    """
    github_username = os.getenv("GITHUB_USERNAME")
    github_token = os.getenv("GITHUB_TOKEN")
    
    # Ensure the credentials are available
    if not github_username or not github_token:
        raise Exception("GitHub credentials are not set in environment variables.")

    # Log in to GHCR
    docker_login(github_username, github_token)
    
    for service, new_tag in services.items():
        # Construct the new image name with tag
        new_image = f"ghcr.io/{github_username}/{service}:{new_tag}"
        # Update the service using Docker service update
        try:
            subprocess.run(["docker", "service", "update", "--image", new_image, service], check=True)
            print(f"Service {service} updated to image {new_image}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to update service {service}: {e}")

class UpdateRequest(BaseModel):
    services: dict  

@router.post("/initiate-update")
async def initiate_update(update_request: UpdateRequest, background_tasks: BackgroundTasks):
    # Using background tasks to not block the API response
    background_tasks.add_task(initiate_update_process, update_request.services)
    return {"message": "Update process initiated"}