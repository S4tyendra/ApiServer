import hmac
import hashlib
import subprocess
import logging
import os
from fastapi import Request, HTTPException
from . import router

SECRET = "x*satya"  # Your webhook secret

def verify_signature(payload_body: bytes, signature_header: str) -> bool:
    """Verify that the webhook payload was sent by GitHub"""
    if not signature_header:
        return False
    
    expected_signature = "sha256=" + hmac.new(
        SECRET.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature_header, expected_signature)

@router.post("/internal/updated")
async def github_webhook(request: Request):
    # Verify GitHub signature
    signature = request.headers.get("X-Hub-Signature-256")
    payload = await request.body()
    
    if not verify_signature(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        # Pull the latest changes
        subprocess.run(["git", "pull"], check=True)
        logging.info("Successfully pulled latest changes from GitHub")
        
        # Execute the restart script in the background
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "restart_server.sh")
        subprocess.Popen([script_path], start_new_session=True)
        
        return {"message": "Updates received and restart initiated"}
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to pull changes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to pull changes")
    except Exception as e:
        logging.error(f"Failed to restart server: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to restart server")
