from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

app = FastAPI(title="Notification Service")

notifications = []

class NotifyRequest(BaseModel):
    user_id: str
    message: str
    type: Optional[str] = "info"

@app.get("/health")
def health():
    return {"status": "notification-service running"}

@app.post("/notify", status_code=201)
def send_notification(req: NotifyRequest):
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": req.user_id,
        "message": req.message,
        "type": req.type,
        "sent_at": datetime.utcnow().isoformat()
    }
    notifications.append(notification)
    print(f"[NOTIFICATION] To: {req.user_id} | {req.type.upper()}: {req.message}")
    return {"message": "Notification sent", "id": notification["id"]}

@app.get("/notifications/{user_id}")
def get_notifications(user_id: str):
    user_notifications = [n for n in notifications if n["user_id"] == user_id]
    if not user_notifications:
        return {"message": "No notifications found", "notifications": []}
    return {"user_id": user_id, "notifications": user_notifications}


from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
