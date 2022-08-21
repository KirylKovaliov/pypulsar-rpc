from datetime import datetime
from pydantic import BaseModel


class RpcResponse(BaseModel):
    message: str
    correlation_id: str
    client_id: str
    server_id: str
    duration: float


class RpcRequest(BaseModel):
    message: str
    correlation_id: str
    callback_topic: str
    client_id: str
    created_at: datetime = datetime.utcnow()
