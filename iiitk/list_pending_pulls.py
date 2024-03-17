from fastapi import APIRouter

router = APIRouter()

import requests


def get_pull_requests(user_name: str):
    data = []
    BASE_URL = "https://api.github.com"
    REPO = "S4tyendra/4thsemnotes"
    TOKEN = "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"
    headers = {"Authorization": f"token {TOKEN}"}

    response = requests.get(
        f"{BASE_URL}/repos/{REPO}/pulls",
        headers=headers,
    )
    if response.status_code == 200:
        pull_requests = response.json()
        for pr in pull_requests:
            name = pr['head']['ref'].split('-')[0]
            if str(name).lower() == str(user_name).lower():
                branch_name = pr['head']['ref']
                description = pr['title']
                data.append(
                    {"Branch Name": branch_name,
                     "Description": description})
    return data


@router.get("/list_pending_pulls")
async def list_pending_pulls(user_id: str):
    return get_pull_requests(user_id)
