TASK: проверка JWT токена на стороне Dash

FILE: src/mko_bi/dash_app.py

GOAL: безопасность фронтенда

IMPLEMENT:

import jwt
from datetime import datetime

def check_token_validity(token: str) -> bool:
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) > datetime.now():
            return True
        return False
    except:
        return False

# в layout или callback
if not check_token_validity(stored_token):
    return dcc.Location(href="/login", id="redirect")

LOGIC:

проверять срок действия токена
реализовать redirect на login при истечении
обновлять токен (refresh token mechanism)

CONSTRAINTS:

проверка валидности токена
автоматический redirect при истечении

DONE:

JWT токен проверяется на валидность
redirect на login работает
