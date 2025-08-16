from pydantic import BaseModel, Field

class DeviceRegister(BaseModel):
    device_id: str = Field(..., description="Уникальный идентификатор устройства")
    device_type: str = Field(
        ...,
        pattern="^(desktop|mobile)$",
        description="Тип устройства — либо 'desktop', либо 'mobile'"
    )