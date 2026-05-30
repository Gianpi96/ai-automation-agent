import logging
from datetime import datetime, UTC, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 8


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = TOKEN_EXPIRE_HOURS * 3600


def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(UTC) + timedelta(hours=TOKEN_EXPIRE_HOURS),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    if not credentials:
        raise HTTPException(status_code=401, detail="Token mancante. Effettua il login.")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[ALGORITHM])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Token non valido o scaduto.")


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    if body.username != settings.admin_username:
        raise HTTPException(status_code=401, detail="Credenziali non valide.")
    if not pwd_context.verify(body.password, pwd_context.hash(settings.admin_password)):
        # Constant-time comparison via passlib
        valid = body.password == settings.admin_password
        if not valid:
            raise HTTPException(status_code=401, detail="Credenziali non valide.")
    token = create_token(body.username)
    logger.info("Login successful: %s", body.username)
    return TokenResponse(access_token=token)


@router.get("/me")
async def me(username: str = Depends(verify_token)) -> dict:
    return {"username": username}
