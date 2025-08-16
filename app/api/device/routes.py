from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.database import get_db
from app.models import User, UserDevice
from app.api.auth.utils import get_current_user 
from app.api.device.schemas import DeviceRegister


router = APIRouter()


@router.post("/device/register")
def register_device(
    payload: DeviceRegister,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    device_id = payload.device_id
    device_type = payload.device_type

    if not device_id or device_type not in ("desktop", "mobile"):
        raise HTTPException(400, "Invalid device_id or device_type")

    # Поиск по ключу
    dev = db.query(UserDevice).filter_by(user_id=user.id, device_id=device_id).first()
    now = datetime.now(timezone.utc)

    if dev:
        dev.last_seen = now
        if dev.device_type != device_type:
            dev.device_type = device_type
    else:
        dev = UserDevice(
            user_id=user.id,
            device_id=device_id,
            device_type=device_type,
            last_seen=now,
        )
        db.add(dev)

    db.commit()
    return {"status": "ok", "device_type": device_type}
