import os
import asyncio
import subprocess
from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Project configurations
projects = {
    "ApiServer": {
        "tmux_session": "1",
        "github_url": "https://github.com/S4tyendra/ApiServer",
        "working_dir": "~/ApiServer",
        "command": "git pull ; hypercorn main:app -b localhost:5001"
    },
    "ai.devh.in": {
        "tmux_session": "0",
        "github_url": "https://github.com/S4tyendra/ai.devh.in",
        "working_dir": "~/ai.devh.in",
        "command": "git pull && pnpm run build && pnpm run start"
    },
    "account.devh.in-v2": {
        "tmux_session": "3",
        "prod_port": "5004",
        "test_port": "3060",
        "github_url": "https://github.com/S4tyendra/account.devh.in-v2",
        "working_dir": "~/account.devh.in-v2",
        "command": "PORT={port} pnpm run start"  # We'll inject the port here
    }
}
HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Manager</title>
    <style>
        {CSS}
    </style>
</head>
<body>
    <h1>Project Manager</h1>
    <div id="projects"></div>
    <div id="output"></div>

    <script>
        {JS}
    </script>
</body>
</html>
"""

CSS = r"""
body {
    font-family: Arial, sans-serif;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

.project {
    border: 1px solid #ddd;
    padding: 10px;
    margin-bottom: 20px;
}

button {
    background-color: #4CAF50;
    border: none;
    color: white;
    padding: 10px 20px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 4px 2px;
    cursor: pointer;
}

#output {
    margin-top: 20px;
    padding: 10px;
    border: 1px solid #ddd;
    background-color: #f9f9f9;
}
"""

JS = r"""
let socket = new WebSocket("ws://" + window.location.host + "/ws");
let projects = {projects};

socket.onmessage = function(event) {
    document.getElementById("output").innerHTML += event.data + "<br>";
};

function updateProject(projectName) {
    socket.send(projectName);
}

function renderProjects() {
    let projectsDiv = document.getElementById("projects");
    for (let [projectName, project] of Object.entries(projects)) {
        projectsDiv.innerHTML += `
            <div class="project">
                <h2>${projectName}</h2>
                <p>GitHub: <a href="${project.github_url}" target="_blank">${project.github_url}</a></p>
                <p>Working Directory: ${project.working_dir}</p>
                <p>Tmux Session: ${project.tmux_session}</p>
                <button onclick="updateProject('${projectName}')">Update and Restart</button>
            </div>
        `;
    }
}

renderProjects();
"""

async def run_command(cmd):
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return stdout, stderr


async def update_project(project_name, ws):
    project = projects[project_name]
    await ws.send_text(f"Updating {project_name}...")
    working_dir = os.path.expanduser(project["working_dir"])
    await ws.send_text(f"Working directory: {working_dir}")

    # Navigate to the working directory
    os.chdir(working_dir)

    if project_name == "account.devh.in-v2":# or project_name == "ai.devh.in":
        await ws.send_text(f"Zero-downtime deployment for {project_name}")
        # Zero-downtime deployment for Next.js app
        prod_session = project["tmux_session"]
        test_session = f"{prod_session}_test"

        await ws.send_text(f"Production session: {prod_session}")
        await ws.send_text(f"Test session: {test_session}")

        # 1. Create new tmux session for test instance
        await ws.send_text("Creating new tmux session for test instance")
        await run_command(f"tmux new-session -d -s {test_session}")
        await ws.send_text("Navigating to working directory")
        await run_command(f"tmux send-keys -t {test_session} 'cd {working_dir}' Enter")

        # 2. Pull latest code and build
        await ws.send_text("Pulling latest code and building")
        await run_command("git pull")
        await ws.send_text("Installing dependencies")
        await run_command("pnpm install")
        await ws.send_text("Building the app")
        await run_command("pnpm run build")

        # 3. Start test instance on test port
        await ws.send_text("Starting test instance")
        test_command = project["command"].format(port=project["test_port"])
        await ws.send_text(f"Test command: {test_command}")
        await run_command(f"tmux send-keys -t {test_session} '{test_command}' Enter")

        # 4. Wait for test instance to start
        await asyncio.sleep(10)

        # 5. Stop production instance
        await ws.send_text("Stopping production instance")
        prod_command = project["command"].format(port=project["prod_port"])
        await ws.send_text(f"Production command: {prod_command}")
        await run_command(f"tmux send-keys -t {prod_session} C-c")

        # 6. Start new production instance
        await ws.send_text("Starting new production instance")
        await run_command(f"tmux send-keys -t {prod_session} '{prod_command}' Enter")

        # 7. Clean up test instance
        await ws.send_text("Cleaning up test instance")
        await asyncio.sleep(5)  # Wait for any remaining connections
        await run_command(f"tmux kill-session -t {test_session}")

        return f"Updated {project_name} with zero downtime"
    else:
        await ws.send_text(f"Regular deployment for {project_name}")
        # Regular deployment for other projects
        tmux_session = project["tmux_session"]
        command = project["command"]
        await ws.send_text(f"Command: {command}")
        await run_command("git pull")
        await run_command(f"tmux send-keys -t {tmux_session} C-c")
        await ws.send_text("Starting the app")
        await run_command(f"tmux send-keys -t {tmux_session} '{command}' Enter")

        return f"Updated and restarted {project_name}"

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    content = HTML.format(CSS=CSS, JS=JS.replace("{projects}", str(projects)))
    return HTMLResponse(content=content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        if data in projects:
            result = await update_project(data, websocket)
            await websocket.send_text(result)
        else:
            await websocket.send_text(f"Unknown project: {data}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
