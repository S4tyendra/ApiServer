import random

import requests
from pydantic import BaseModel
import base64

def get_main_branch_sha():
    BASE_URL = "https://api.github.com"
    REPO = "S4tyendra/NOTES-res"
    TOKEN = "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"
    headers = {"Authorization": f"token {TOKEN}"}

    response = requests.get(f"{BASE_URL}/repos/{REPO}/branches/new", headers=headers)
    response_json = response.json()

    if response.status_code == 200:
        sha = response_json["commit"]["sha"]
        return sha
    else:
        print(f"Failed to get SHA of the new branch. Status code: {response.status_code}")
        return None


def create_branch(_id):
    BASE_URL = "https://api.github.com"
    REPO = "S4tyendra/NOTES-res"
    TOKEN = "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"
    BRANCH_NAME = _id + "-" + str(random.randint(1000, 9999))
    headers = {"Authorization": f"token {TOKEN}"}

    sha = get_main_branch_sha()
    if sha:
        payload = {"ref": f"refs/heads/{BRANCH_NAME}", "sha": sha}
        response = requests.post(f"{BASE_URL}/repos/{REPO}/git/refs", headers=headers, json=payload)

        if response.status_code == 201:
            print(f"Branch '{BRANCH_NAME}' created successfully!")
            return BRANCH_NAME
        else:
            print(f"Failed to create branch '{BRANCH_NAME}'. Status code: {response.status_code}")
            return None
    else:
        return None


def delete_file_or_folder(branch_name, file_path, _id):
    BASE_URL = "https://api.github.com"
    REPO = "S4tyendra/NOTES-res"
    TOKEN = "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"
    headers = {"Authorization": f"token {TOKEN}"}

    response = requests.get(
        f"{BASE_URL}/repos/{REPO}/contents{file_path}?ref={branch_name}",
        headers=headers
    )
    if response.status_code == 200:
        sha = response.json().get('sha')
        if sha:
            delete_payload = {
                "branch": branch_name,
                "message": f"Delete {file_path}",
                "sha": sha,
                "committer": {"name": _id, "email": f"{_id}@iiitkota.ac.in"}
            }
            delete_response = requests.delete(
                f"{BASE_URL}/repos/{REPO}/contents{file_path}",
                headers=headers,
                json=delete_payload,
            )
            if delete_response.status_code == 200:
                print("File/Folder deleted successfully!")
            else:
                print(f"Failed to delete file/folder. Status code: {delete_response.status_code}")
        else:
            print("Failed to retrieve SHA for the file/folder in the specified branch")
    else:
        print(
            f"Failed to retrieve file/folder information from the specified branch. Status code: {response.status_code}")
    return f"Delete {file_path}"


def create_pull_request(branch_name, pull_request_title):
    BASE_URL = "https://api.github.com"
    REPO = "S4tyendra/NOTES-res"
    TOKEN = "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"
    headers = {"Authorization": f"token {TOKEN}"}

    payload = {
        "title": pull_request_title,
        "head": branch_name,
        "base": "new",
        "body": f"Generated pull request of {pull_request_title}",
    }
    response = requests.post(
        f"{BASE_URL}/repos/{REPO}/pulls",
        headers=headers,
        json=payload,
    )
    if response.status_code == 201:
        print("Pull request created successfully!")
    else:
        print(f"Failed to create pull request. Status code: {response.status_code}")


def delete_file(user_id, path):
    branch_name = create_branch(user_id)
    if branch_name:
        name = delete_file_or_folder(branch_name, path, user_id)
        create_pull_request(branch_name, name)
        return "Request successful!"
    else:
        return "Request failed!"


class DeleteData(BaseModel):
    user_id: str
    file_path: str


from fastapi import APIRouter

router = APIRouter()


@router.delete("/delete_file")
async def delete__file(data: DeleteData):
    rt = delete_file(data.user_id, data.file_path)
    return rt


def edit_file_or_folder(branch_name, file_path, new_content, _id):
    BASE_URL = "https://api.github.com"
    REPO = "S4tyendra/NOTES-res"
    TOKEN = "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"
    headers = {"Authorization": f"token {TOKEN}"}

    response = requests.get(
        f"{BASE_URL}/repos/{REPO}/contents{file_path}?ref={branch_name}",
        headers=headers
    )
    if response.status_code == 200:
        file_info = response.json()
        sha = file_info.get('sha')
        if sha:
            # Prepare the new content
            new_content_encoded = base64.b64encode(new_content.encode()).decode()
            edit_payload = {
                "branch": branch_name,
                "message": f"Edit {file_path}",
                "content": new_content_encoded,
                "sha": sha,
                "committer": {"name": _id, "email": f"{_id}@iiitkota.ac.in"}
            }
            # Send a PUT request to update the file
            edit_response = requests.put(
                f"{BASE_URL}/repos/{REPO}/contents{file_path}",
                headers=headers,
                json=edit_payload,
            )
            if edit_response.status_code == 200:
                print("File/Folder edited successfully!")
            else:
                print(f"Failed to edit file/folder. Status code: {edit_response.status_code}")
        else:
            print("Failed to retrieve SHA for the file/folder in the specified branch")
    else:
        print(
            f"Failed to retrieve file/folder information from the specified branch. Status code: {response.status_code}")


def edit_file(user_id, path, new_content):
    branch_name = create_branch(user_id)
    if branch_name:
        edit_file_or_folder(branch_name, path, new_content, user_id)
        create_pull_request(branch_name, f"Edit {path}")
        return "File edited successfully!"
    else:
        return "Failed to create branch. File editing aborted."


class EditData(BaseModel):
    user_id: str
    file_path: str
    new_content: str


@router.put("/edit_file")
async def edit__file(data: EditData):
    rt = edit_file(data.user_id, data.file_path, data.new_content)
    return rt

def create_file_or_folder(branch_name, file_path, file_name, content, _id):
    BASE_URL = "https://api.github.com"
    REPO = "S4tyendra/NOTES-res"
    TOKEN = "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"
    headers = {"Authorization": f"token {TOKEN}"}

    response = requests.get(
        f"{BASE_URL}/repos/{REPO}/contents{file_path}?ref={branch_name}",
        headers=headers
    )
    if response.status_code == 200:
        print(f"File or folder '{file_path}' already exists. Aborting creation.")
        return
    elif response.status_code == 404:
        # Prepare the new file content
        content_encoded = base64.b64encode(content.encode()).decode()
        create_payload = {
            "branch": branch_name,
            "message": f"Create {file_name}",
            "content": content_encoded,
            "committer": {"name": _id, "email": f"{_id}@iiitkota.ac.in"}
        }
        # Send a PUT request to create the file
        create_response = requests.put(
            f"{BASE_URL}/repos/{REPO}/contents{file_path}",
            headers=headers,
            json=create_payload,
        )
        if create_response.status_code == 201:
            print(f"File '{file_name}' created successfully!")
        else:
            print(f"Failed to create file '{file_name}'. Status code: {create_response.status_code}")
    else:
        print(f"Failed to check if file/folder exists. Status code: {response.status_code}")

def create_file(user_id, path, file_name, content):
    branch_name = create_branch(user_id)
    if branch_name:
        file_path = f"{path}/{file_name}"
        create_file_or_folder(branch_name, file_path, file_name, content, user_id)
        create_pull_request(branch_name, f"Create {file_name}")
        return "File created successfully!"
    else:
        return "Failed to create branch. File creation aborted."

class CreateFileData(BaseModel):
    user_id: str
    path: str
    file_name: str
    content: str

@router.put("/create_file")
async def create__file(data: CreateFileData):
    rt = create_file(data.user_id, data.path, data.file_name, data.content)
    return rt
