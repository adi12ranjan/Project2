from pydantic import BaseModel
from typing import Optional


class RawEmailRequest(BaseModel):
    raw_email: str
    filename: Optional[str] = 'pasted-email.eml'


class DemoRequest(BaseModel):
    demo_id: str  # 'demo1' | 'demo2' | 'demo3' | 'demo4'
