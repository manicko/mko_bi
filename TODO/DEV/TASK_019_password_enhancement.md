TASK: улучшение обработки паролей

FILE: src/mko_bi/core/security.py

GOAL: поддержка паролей длиннее 72 байт

IMPLEMENT:

import hashlib

def _prehash_password(password: str) -> bytes:
    # SHA256 before bcrypt (рекомендация)
    return hashlib.sha256(password.encode()).digest()

def hash_password(password: str) -> str:
    # pre-hash если пароль длинный
    if len(password.encode()) > 72:
        pwd_bytes = _prehash_password(password)
    else:
        pwd_bytes = password.encode()
    
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if len(plain_password.encode()) > 72:
            pwd_bytes = _prehash_password(plain_password)
        else:
            pwd_bytes = plain_password.encode()
        
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode())
    except Exception:
        return False

LOGIC:

добавить pre-hash (SHA256) перед bcrypt
обрабатывать пароли длиннее 72 байт
документировать ограничения

CONSTRAINTS:

обратная совместимость с существующими паролями
корректная проверка паролей

DONE:

пароли длиннее 72 байт поддерживаются
существующие пароли работают
