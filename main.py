import asyncio
import json
import logging
import os
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import psutil
import platform

from starlette.responses import HTMLResponse, StreamingResponse
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from api import api
from auth.google import router as google_router
from functions.db import db_connect, db_close
from iiitkres import router as iiitkres_router
from stripe_pay.payments import router as stripe_router
from auth.login import router as auth_router
from user.profile import router as user_router
from pytz import timezone
from ai.ai import router as ai_router
from apps import router as apps_router


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('app.log'), logging.StreamHandler()])

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")




@app.on_event("startup")
async def startup_event():
    await db_connect()
    logging.info("Connected to databse!")

@app.on_event("shutdown")
async def shutdown_db_client():
    await db_close()


async def clear_log():
    pass


def delete_temp():
    for file in os.listdir("temp"):
        if file.endswith(".pdf"):
            os.remove(f"temp/{file}")


# Set up scheduler
scheduler = AsyncIOScheduler()
scheduler.add_job(clear_log, 'interval', minutes=10)
scheduler.add_job(delete_temp, 'interval', minutes=5)
scheduler.start()
logging.info("Scheduler started!")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://account.devh.in"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from datetime import datetime
import pytz

ist = pytz.timezone('Asia/Kolkata')


# Global variables
start_time = time.time()
request_count = 0
total_bandwidth = 0

# Middleware
@app.middleware("http")
async def log_request(request: Request, call_next):
    global request_count, total_bandwidth
    global start_time
    start_time = time.time()
    # await asyncio.sleep(14)
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    request_count += 1

    if isinstance(response, StreamingResponse):
        # For streaming responses, we can't get the content length directly
        # We'll need to wrap the response to count the bytes as they're sent
        original_body = response.body_iterator

        async def wrapped_body():
            global total_bandwidth
            async for chunk in original_body:
                total_bandwidth += len(chunk)
                yield chunk

        response.body_iterator = wrapped_body()
    else:
        # For regular responses, we can get the content length directly
        try:
            total_bandwidth += len(response.body)
        except:
            pass

    logging.debug(
        f"{request.method} - {request.url} / {request.headers.get('cookie')} /{request.headers.get('x-api-key')}")
    return response



if os.path.exists(".env"):
    from dotenv import load_dotenv

    load_dotenv()

app.include_router(user_router, tags=["user"], prefix="/user")
app.include_router(api, tags=[
    "API", ], prefix="/api")
app.include_router(stripe_router, tags=["stripe"], prefix="/stripe", include_in_schema=False)
app.include_router(google_router, tags=["GAUTH"], prefix="/auth", include_in_schema=False)
app.include_router(iiitkres_router, tags=["IIITK RES"], prefix="/iiitk")
app.include_router(auth_router, tags=["Auth"], prefix="/auth")
app.include_router(ai_router, tags=["AI"], prefix="/ai")
app.include_router(apps_router, tags=["Apps"], prefix="/apps")



@app.get("/", include_in_schema=False)
async def root(request: Request, response: Response):
    return RedirectResponse("https://account.devh.in/")
@app.get("/health", response_class=HTMLResponse)
async def health_check():
    current_time = datetime.now()
    uptime = time.time() - start_time
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent

    html_content = f"""
    <html>
    <head>
        <title>Server Health Check Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-color: #1a1a1a;
                --text-color: #e0e0e0;
                --accent-color: #4CAF50;
                --card-bg: #2a2a2a;
                --hover-color: #3a3a3a;
            }}
            body {{
                font-family: 'Roboto', Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: var(--bg-color);
                color: var(--text-color);
                line-height: 1.6;
            }}
            main {{
                max-width: 1200px;
                margin: 2rem auto;
                padding: 0 1rem;
            }}
            h1 {{
                color: var(--accent-color);
                text-align: center;
                margin-bottom: 2rem;
            }}
            .summary {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
                margin-bottom: 2rem;
            }}
            .summary-card {{
                background-color: var(--card-bg);
                padding: 1rem;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }}
            .summary-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 6px 8px rgba(0,0,0,0.15);
            }}
            .summary-card h3 {{
                margin-top: 0;
                color: var(--accent-color);
            }}
            .metrics-container {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1rem;
            }}
            .metric-card {{
                background-color: var(--card-bg);
                padding: 1rem;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }}
            .metric-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 6px 8px rgba(0,0,0,0.15);
            }}
            .metric-card h3 {{
                margin-top: 0;
                color: var(--accent-color);
                display: flex;
                align-items: center;
            }}
            .metric-card h3 i {{
                margin-right: 0.5rem;
            }}
            .metric-value {{
                font-size: 1.2rem;
                font-weight: bold;
            }}
            .update-button {{
                display: block;
                width: 100%;
                max-width: 300px;
                margin: 2rem auto;
                padding: 0.8rem;
                font-size: 1rem;
                color: #fff;
                background-color: var(--accent-color);
                border: none;
                border-radius: 4px;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }}
            .update-button:active {{
                transform: scale(0.98);
            }}
            #exportButton {{
                display: block;
                width: 100%;
                max-width: 300px;
                margin: 2rem auto;
                padding: 0.8rem;
                font-size: 1rem;
                color: #fff;
                background-color: var(--accent-color);
                border: none;
                border-radius: 4px;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }}
            .btn-danger {{
                background-color: #f44336;
            }}
        </style>
    </head>
    <body>
        <main>
            <h1>Server Health Check Dashboard</h1>

            <section class="summary">
                <div class="summary-card">
                    <h3>CPU Usage</h3>
                    <div class="metric-value" id="cpu_usage_summary">{cpu_usage}%</div>
                </div>
                <div class="summary-card">
                    <h3>Memory Usage</h3>
                    <div class="metric-value" id="memory_usage_summary">{memory_usage}%</div>
                </div>
                <div class="summary-card">
                    <h3>Disk Usage</h3>
                    <div class="metric-value" id="disk_usage_summary">{disk_usage}%</div>
                </div>
                <div class="summary-card">
                    <h3>Total Requests</h3>
                    <div class="metric-value" id="total_requests_summary">{request_count}</div>
                </div>
            </section>

            <button id="updateButton" onclick="toggleUpdate()" class="update-button">Start Real-time Updates</button>

            <section class="metrics-container">
                <div class="metric-card">
                    <h3><i class="fas fa-clock"></i> Server Start Time</h3>
                    <div class="metric-value" id="server_start_time">{datetime.fromtimestamp(start_time)}</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-clock"></i> Current Server Time</h3>
                    <div class="metric-value" id="current_server_time">{current_time}</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-hourglass-half"></i> Uptime</h3>
                    <div class="metric-value" id="uptime">{uptime:.2f} seconds</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-exchange-alt"></i> Total Requests</h3>
                    <div class="metric-value" id="total_requests">{request_count}</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-network-wired"></i> Total Bandwidth Used</h3>
                    <div class="metric-value" id="total_bandwidth">{total_bandwidth / (1024 * 1024):.2f} MB</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-microchip"></i> CPU Usage</h3>
                    <div class="metric-value" id="cpu_usage">{cpu_usage}%</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-memory"></i> Memory Usage</h3>
                    <div class="metric-value" id="memory_usage">{memory_usage}%</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-hdd"></i> Disk Usage</h3>
                    <div class="metric-value" id="disk_usage">{disk_usage}%</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-desktop"></i> Operating System</h3>
                    <div class="metric-value" id="operating_system">{platform.system()} {platform.release()}</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fab fa-python"></i> Python Version</h3>
                    <div class="metric-value" id="python_version">{platform.python_version()}</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-microchip"></i> Processor</h3>
                    <div class="metric-value" id="processor">{platform.processor()}</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-microchip"></i> Number of CPU Cores</h3>
                    <div class="metric-value" id="cpu_cores">{psutil.cpu_count()}</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-memory"></i> Total RAM</h3>
                    <div class="metric-value" id="total_ram">{psutil.virtual_memory().total / (1024 * 1024 * 1024):.2f} GB</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-network-wired"></i> Network Interfaces</h3>
                    <div class="metric-value" id="network_interfaces">{', '.join(psutil.net_if_addrs().keys())}</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-hdd"></i> Disk Partitions</h3>
                    <div class="metric-value" id="disk_partitions">{', '.join([p.mountpoint for p in psutil.disk_partitions()])}</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-power-off"></i> Boot Time</h3>
                    <div class="metric-value" id="boot_time">{datetime.fromtimestamp(psutil.boot_time())}</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-folder"></i> Current Working Directory</h3>
                    <div class="metric-value" id="current_working_directory">{os.getcwd()}</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-cogs"></i> Environment Variables</h3>
                    <div class="metric-value" id="environment_variables">{len(os.environ)} variables</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-globe"></i> Server Timezone</h3>
                    <div class="metric-value" id="server_timezone">{time.tzname}</div>
                </div>
            </section>
        </main>
        <script>
            let eventSource;

            function updateTable(data) {{
                for (const [key, value] of Object.entries(data)) {{
                    const element = document.getElementById(key);
                    if (element) {{
                        const oldValue = element.textContent;
                        element.textContent = value;
                        
                    }}
                    // Update summary cards
                    const summaryElement = document.getElementById(`${{key}}_summary`);
                    if (summaryElement) {{
                        summaryElement.textContent = value;
                    }}
                }}
            }}

            function toggleUpdate() {{
    const button = document.getElementById('updateButton');
    if (button.textContent === 'Start Real-time Updates') {{
        button.classList.add('btn-danger');
        eventSource = new EventSource("/health_stream");
        eventSource.onmessage = function(event) {{
            const data = JSON.parse(event.data);
            updateTable(data);
        }};
        button.textContent = 'Stop Real-time Updates';
    }} else {{
        if (eventSource) {{
            eventSource.close();
        }}
        button.textContent = 'Start Real-time Updates';
        button.classList.remove('btn-danger');
    }}
}}

            // Keyboard shortcut
            document.addEventListener('keydown', function(event) {{
                if (event.ctrlKey && event.key === 'u') {{
                    toggleUpdate();
                }}
            }});

            // Tooltips
            const metrics = document.querySelectorAll('.metric-card');
            metrics.forEach(metric => {{
                const title = metric.querySelector('h3').textContent;
                const value = metric.querySelector('.metric-value').textContent;
                metric.title = `${{title}}: ${{value}}`;
            }});

            // Export functionality
            function exportData() {{
                const data = {{}};
                metrics.forEach(metric => {{
                    const key = metric.querySelector('h3').textContent.trim();
                    const value = metric.querySelector('.metric-value').textContent.trim();
                    data[key] = value;
                }});
                const jsonString = JSON.stringify(data, null, 2);
                const blob = new Blob([jsonString], {{ type: 'application/json' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'server_health_data.json';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }}

            // Add export button
            const exportButton = document.createElement('button');
            exportButton.textContent = 'Export Data';
            exportButton.onclick = exportData;
            exportButton.style.marginTop = '1rem';
            document.querySelector('main').appendChild(exportButton);
            exportButton.id = 'exportButton';
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

security = HTTPBasic()

def check_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = "satya"
    correct_password = "satyendra"
    is_correct_username = secrets.compare_digest(credentials.username, correct_username)
    is_correct_password = secrets.compare_digest(credentials.password, correct_password)
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/health_stream", dependencies=[Depends(check_credentials)])
async def health_stream():
    async def event_generator():
        while True:
            current_time = datetime.now()
            uptime = time.time() - start_time
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent

            data = {
                "server_start_time": datetime.fromtimestamp(start_time).isoformat(),
                "current_server_time": current_time.isoformat(),
                "uptime": f"{uptime:.2f} seconds",
                "total_requests": request_count,
                "total_bandwidth": f"{total_bandwidth / (1024 * 1024):.2f} MB",
                "cpu_usage": f"{cpu_usage}%",
                "memory_usage": f"{memory_usage}%",
                "disk_usage": f"{disk_usage}%",
                "operating_system": f"{platform.system()} {platform.release()}",
                "python_version": platform.python_version(),
                "processor": platform.processor(),
                "cpu_cores": psutil.cpu_count(),
                "total_ram": f"{psutil.virtual_memory().total / (1024 * 1024 * 1024):.2f} GB",
                "network_interfaces": ", ".join(psutil.net_if_addrs().keys()),
                "disk_partitions": ", ".join([p.mountpoint for p in psutil.disk_partitions()]),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                "current_working_directory": os.getcwd(),
                "environment_variables": f"{len(os.environ)} variables",
                "server_timezone": str(time.tzname),
            }

            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")






async def delete_file(file_path: str, ):
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True, port=8000)

