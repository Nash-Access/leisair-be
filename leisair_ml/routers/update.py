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
    result = subprocess.run(login_command, input=token, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to log in to GHCR: {result.stderr}")
    
def find_services_using_image(image_name: str) -> list:
    """
    Placeholder function to determine which services in 'docker-compose.yml' are using a specific image.
    This needs to be implemented based on your project's configuration.

    Args:
        image_name (str): The name of the image to check.

    Returns:
        A list of service names using the specified image.
    """
    # Example implementation
    if image_name == "leisair-ml":
        return ["worker", "fastapi"]
    elif image_name == "leisair-nextjs":
        return ["leisair-nextjs"]
    else:
        return []
    
def initiate_update_process(images_with_tags: dict):
    """
    Updates services that use specified images to the new image tags by pulling the latest images and recreating the services.

    Args:
        images_with_tags (dict): A dictionary of image names and their corresponding new tags.
    """
    github_username = os.getenv("GITHUB_USERNAME")
    github_token = os.getenv("GITHUB_TOKEN")
    
    if not github_username or not github_token:
        raise Exception("GitHub credentials are not set in environment variables.")

    # Log in to GHCR
    docker_login(github_username, github_token)

    for image, new_tag in images_with_tags.items():
        # Pull the latest image version
        new_image = f"ghcr.io/{github_username}/{image}:{new_tag}"
        print(f"Pulling the latest image for {image}: {new_image}")
        subprocess.run(["docker", "pull", new_image], check=True)

        # Determine which services need to be updated based on the image they use
        services_to_update = find_services_using_image(image)

        # Recreate each service with the new image version
        for service in services_to_update:
            print(f"Recreating {service} with the latest image: {new_image}")
            # In Docker Compose, use 'docker-compose up -d' to recreate the service
            subprocess.run(["docker-compose", "up", "-d", "--force-recreate", service], check=True)

            print(f"Service {service} has been updated to use the latest image version: {new_image}.")

# def initiate_update_process(services: dict):
#     """
#     Initiates the update process for given services with their new tags.
#     Includes a Docker login to GHCR using environment variables.

#     Args:
#     services (dict): A dictionary of service names and their corresponding new image tags.
#     """
#     github_username = os.getenv("GITHUB_USERNAME")
#     github_token = os.getenv("GITHUB_TOKEN")
    
#     # Ensure the credentials are available
#     if not github_username or not github_token:
#         raise Exception("GitHub credentials are not set in environment variables.")

#     # Log in to GHCR
#     docker_login(github_username, github_token)

#     services_to_update = {}

#     # Iterate over the services and their new tags
#     for service, new_tag in services.items():
#         if service == "leisair-ml":
#             services_to_update["worker"] = new_tag
#             services_to_update["fastapi"] = new_tag
#         elif service == "leisair-nextjs":
#             services_to_update["leisair-nextjs"] = new_tag
    
#     service_map = {
#         "leisair-nextjs": "leisair-nextjs",
#         "worker": "leisair-ml",
#         "fastapi": "leisair-ml"
#     }

#     for service, new_tag in services_to_update.items():
#         # Construct the new image name with tag
#         new_image = f"ghcr.io/{github_username}/{service_map[service]}:{new_tag}"
#         # Update the service using Docker service update
#         try:
#             subprocess.run(["docker", "service", "update", "--image", new_image, service], check=True)
#             print(f"Service {service} updated to image {new_image}")
#         except subprocess.CalledProcessError as e:
#             print(f"Failed to update service {service}: {e}")

class UpdateRequest(BaseModel):
    services: dict  

@router.post("/initiate-update")
async def initiate_update(update_request: UpdateRequest, background_tasks: BackgroundTasks):
    print("Received update request:", update_request)
    # Using background tasks to not block the API response
    background_tasks.add_task(initiate_update_process, update_request.services)
    return {"message": "Update process initiated"}