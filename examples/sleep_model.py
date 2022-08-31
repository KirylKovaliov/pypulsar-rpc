from pydantic import BaseModel


class SleepRequest(BaseModel):
    time: int


class SleepResponse(BaseModel):
    status: int
    message: str
