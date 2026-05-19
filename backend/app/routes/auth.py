# app/routes/auth.py (фрагмент с логированием)
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import AuthResponse, LoginRequest, UserCreate
from app.security import create_access_token, hash_password, verify_password
from app.validators import ensure_profile_payload_allowed, ensure_public_role, normalize_role

logger = logging.getLogger("psychology-api.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


def _dump_schema(schema):
    if hasattr(schema, "model_dump"):
        return schema.model_dump()
    return schema.dict()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    data = _dump_schema(payload)
    role = normalize_role(data["role"])
    
    logger.info("Registration attempt", extra={"username": data["username"], "email": data["email"], "role": role})
    
    try:
        ensure_public_role(role)
        ensure_profile_payload_allowed(
            role,
            {key for key, value in data.items() if value is not None and key not in {"username", "email", "password", "role"}},
        )
    except ValueError as exc:
        logger.warning("Registration validation failed", extra={"reason": str(exc)})
        raise HTTPException(status_code=400, detail=str(exc))

    existing_user = (
        db.query(User)
        .filter(or_(User.username == data["username"], User.email == data["email"]))
        .first()
    )
    if existing_user:
        logger.warning("Registration failed: user already exists", extra={"username": data["username"], "email": data["email"]})
        raise HTTPException(status_code=400, detail="Пользователь с таким ником или email уже существует")

    user = User(
        username=data["username"],
        email=data["email"],
        hashed_password=hash_password(data["password"]),
        role=role,
        full_name=data.get("full_name"),
        specialization=data.get("specialization"),
        education=data.get("education"),
        about=data.get("about"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info("User registered successfully", extra={"user_id": user.id, "username": user.username})
    return {"access_token": create_access_token(user), "user": user}


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    logger.info("Login attempt", extra={"username": payload.username})
    
    user = (
        db.query(User)
        .filter(or_(User.username == payload.username, User.email == payload.username))
        .first()
    )
    if not user or not verify_password(payload.password, user.hashed_password):
        logger.warning("Login failed: invalid credentials", extra={"username": payload.username})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )

    logger.info("Login successful", extra={"user_id": user.id, "username": user.username, "role": user.role})
    return {"access_token": create_access_token(user), "user": user}