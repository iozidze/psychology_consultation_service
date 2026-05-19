from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Note, Recommendation, Review, Slot, User
from app.schemas import AdminUserCreate, ProfileUpdate, UserRead
from app.security import get_current_user, hash_password, require_roles
from app.validators import ensure_profile_payload_allowed, normalize_role

router = APIRouter(prefix="/users", tags=["users"])


def _dump_schema(schema, **kwargs):
    if hasattr(schema, "model_dump"):
        return schema.model_dump(**kwargs)
    return schema.dict(**kwargs)


def _fields_set(schema) -> set[str]:
    return set(getattr(schema, "model_fields_set", getattr(schema, "__fields_set__", set())))


@router.get("/me", response_model=UserRead)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserRead)
def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = _dump_schema(payload, exclude_unset=True)
    try:
        ensure_profile_payload_allowed(current_user.role, _fields_set(payload))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    for field, value in data.items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/search", response_model=list[UserRead])
def search_users(
    q: str = Query(min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del current_user
    search = f"%{q.strip()}%"
    return (
        db.query(User)
        .filter(
            or_(
                User.username.ilike(search),
                (User.role == "psychologist") & User.full_name.ilike(search),
            )
        )
        .order_by(User.role.desc(), User.username)
        .limit(20)
        .all()
    )


@router.get("/clients", response_model=list[UserRead])
def get_clients(
    current_user: User = Depends(require_roles("psychologist", "admin")),
    db: Session = Depends(get_db),
):
    del current_user
    return db.query(User).filter(User.role == "client").order_by(User.username).all()


@router.get("/", response_model=list[UserRead])
def get_users(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    del current_user
    return db.query(User).order_by(User.role, User.username).all()


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AdminUserCreate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    del current_user
    data = _dump_schema(payload)
    role = normalize_role(data["role"])
    try:
        profile_fields = {
            key
            for key, value in data.items()
            if value is not None and key not in {"username", "email", "password", "role"}
        }
        ensure_profile_payload_allowed(role, profile_fields)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    existing_user = (
        db.query(User)
        .filter(or_(User.username == data["username"], User.email == data["email"]))
        .first()
    )
    if existing_user:
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
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Администратор не может удалить сам себя")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    db.query(Note).filter(or_(Note.author_id == user_id, Note.client_id == user_id)).delete(synchronize_session=False)
    db.query(Recommendation).filter(
        or_(Recommendation.psychologist_id == user_id, Recommendation.client_id == user_id)
    ).delete(synchronize_session=False)
    db.query(Review).filter(
        or_(Review.psychologist_id == user_id, Review.client_id == user_id)
    ).delete(synchronize_session=False)
    db.query(Slot).filter(Slot.psychologist_id == user_id).delete(synchronize_session=False)
    db.query(Slot).filter(Slot.client_id == user_id).update({"client_id": None}, synchronize_session=False)
    db.delete(user)
    db.commit()
