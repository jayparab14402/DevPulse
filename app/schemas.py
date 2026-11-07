'''

{
  "service": "auth-service",
  "level": "ERROR",
  "message": "Database connection timeout",
  "status_code": 500
}

1. app/ ke andar ek alag file banao for Pydantic schema, something like schemas.py.
2. Ek model banao jo above fields validate kare.
3. level ko initially simple string rehne do.
4. status_code optional hona chahiye, because har incident HTTP-based nahi hoga.
5. main.py mein POST /events endpoint banao.
6. Abhi database nahi hai, so jo request aayi wahi validated response mein return kar do.
7. Swagger /docs se test karo.
'''

from pydantic import BaseModel
from typing import Literal

class Auth(BaseModel):
    service: str
    level: Literal["INFO", "WARNING", "ERROR", "CRITICAL"]
    message: str
    status_code: int | None