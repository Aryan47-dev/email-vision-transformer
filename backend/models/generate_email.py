from pydantic import BaseModel


class GenerateEmailResult(BaseModel):
    html: str
