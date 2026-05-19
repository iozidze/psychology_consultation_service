from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Slot, User
from app.schemas import SlotCreate, SlotRead, SlotUpdate
from app.security import get_current_user, require_roles
from app.validators import validate_slot_window

router = APIRouter(prefix="/slots", tags=["slots"])


def _dump_schema(schema, **kwargs):
    if hasattr(schema, "model_dump"):
        return schema.model_dump(**kwargs)
    return schema.dict(**kwargs)


def _find_overlapping_psychologist_slot(
    db: Session,
    psychologist_id: int,
    start_at,
    end_at,
    exclude_slot_id: int | None = None,
):
    query = db.query(Slot).filter(
        Slot.psychologist_id == psychologist_id,
        Slot.start_at < end_at,
        Slot.end_at > start_at,
    )
    if exclude_slot_id:
        query = query.filter(Slot.id != exclude_slot_id)
    return query.first()


def _find_overlapping_client_slot(
    db: Session,
    client_id: int,
    start_at,
    end_at,
    exclude_slot_id: int | None = None,
):
    query = db.query(Slot).filter(
        Slot.client_id == client_id,
        Slot.start_at < end_at,
        Slot.end_at > start_at,
    )
    if exclude_slot_id:
        query = query.filter(Slot.id != exclude_slot_id)
    return query.first()


def _serialize_slot(slot: Slot, current_user: User) -> dict:
    include_link = (
        current_user.role == "admin"
        or slot.psychologist_id == current_user.id
        or slot.client_id == current_user.id
    )
    return {
        "id": slot.id,
        "psychologist_id": slot.psychologist_id,
        "psychologist_username": slot.psychologist.username,
        "psychologist_full_name": slot.psychologist.full_name,
        "client_id": slot.client_id,
        "client_username": slot.client.username if slot.client else None,
        "start_at": slot.start_at,
        "end_at": slot.end_at,
        "specialization": slot.specialization,
        "meeting_link": slot.meeting_link if include_link else None,
        "is_booked": slot.client_id is not None,
    }


@router.get("/", response_model=list[SlotRead])
def get_slots(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    slots = db.query(Slot).order_by(Slot.start_at).all()
    return [_serialize_slot(slot, current_user) for slot in slots]


@router.post("/", response_model=SlotRead, status_code=status.HTTP_201_CREATED)
def create_slot(
    payload: SlotCreate,
    current_user: User = Depends(require_roles("psychologist")),
    db: Session = Depends(get_db),
):
    try:
        validate_slot_window(payload.start_at, payload.end_at)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if _find_overlapping_psychologist_slot(db, current_user.id, payload.start_at, payload.end_at):
        raise HTTPException(status_code=400, detail="Слот пересекается с другим слотом психолога")

    slot = Slot(
        psychologist_id=current_user.id,
        start_at=payload.start_at,
        end_at=payload.end_at,
        specialization=payload.specialization,
        meeting_link=payload.meeting_link,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return _serialize_slot(slot, current_user)


@router.put("/{slot_id}", response_model=SlotRead)
def update_slot(
    slot_id: int,
    payload: SlotUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    slot = db.get(Slot, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Слот не найден")
    if current_user.role != "admin" and slot.psychologist_id != current_user.id:
        raise HTTPException(status_code=403, detail="Можно редактировать только свои слоты")

    data = _dump_schema(payload, exclude_unset=True)
    start_at = data.get("start_at", slot.start_at)
    end_at = data.get("end_at", slot.end_at)
    try:
        validate_slot_window(start_at, end_at)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if _find_overlapping_psychologist_slot(db, slot.psychologist_id, start_at, end_at, slot.id):
        raise HTTPException(status_code=400, detail="Слот пересекается с другим слотом психолога")
    if slot.client_id and _find_overlapping_client_slot(db, slot.client_id, start_at, end_at, slot.id):
        raise HTTPException(status_code=400, detail="Новое время пересекается с записью клиента")

    for field, value in data.items():
        setattr(slot, field, value)
    db.commit()
    db.refresh(slot)
    return _serialize_slot(slot, current_user)


@router.post("/{slot_id}/book", response_model=SlotRead)
def book_slot(
    slot_id: int,
    current_user: User = Depends(require_roles("client")),
    db: Session = Depends(get_db),
):
    slot = db.get(Slot, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Слот не найден")
    if slot.client_id is not None:
        raise HTTPException(status_code=400, detail="Слот уже занят")
    if _find_overlapping_client_slot(db, current_user.id, slot.start_at, slot.end_at):
        raise HTTPException(status_code=400, detail="У клиента уже есть запись на это время")

    slot.client_id = current_user.id
    db.commit()
    db.refresh(slot)
    return _serialize_slot(slot, current_user)


@router.delete("/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_slot(
    slot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    slot = db.get(Slot, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Слот не найден")
    if current_user.role != "admin" and slot.psychologist_id != current_user.id:
        raise HTTPException(status_code=403, detail="Можно удалить только свой слот")
    if slot.client_id and current_user.role != "admin":
        raise HTTPException(status_code=400, detail="Нельзя удалить занятый слот без администратора")

    db.delete(slot)
    db.commit()
