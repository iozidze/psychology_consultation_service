from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Note, Recommendation, Review, Slot, User
from app.schemas import (
    NoteCreate,
    NoteRead,
    NoteUpdate,
    RecommendationCreate,
    RecommendationRead,
    ReviewCreate,
    ReviewRead,
)
from app.security import get_current_user, require_roles

router = APIRouter(prefix="/notes", tags=["notes"])


def _serialize_note(note: Note) -> dict:
    return {
        "id": note.id,
        "author_id": note.author_id,
        "author_username": note.author.username,
        "client_id": note.client_id,
        "client_username": note.client.username,
        "kind": note.kind,
        "text": note.text,
        "created_at": note.created_at,
        "updated_at": note.updated_at,
    }


def _serialize_recommendation(recommendation: Recommendation) -> dict:
    return {
        "id": recommendation.id,
        "psychologist_id": recommendation.psychologist_id,
        "psychologist_username": recommendation.psychologist.username,
        "psychologist_full_name": recommendation.psychologist.full_name,
        "client_id": recommendation.client_id,
        "client_username": recommendation.client.username,
        "text": recommendation.text,
        "created_at": recommendation.created_at,
    }


def _recalculate_rating(db: Session, psychologist: User) -> None:
    reviews = db.query(Review).filter(Review.psychologist_id == psychologist.id).all()
    psychologist.rating_count = len(reviews)
    psychologist.rating = round(sum(review.rating for review in reviews) / len(reviews), 2) if reviews else 0


@router.get("/", response_model=list[NoteRead])
def get_notes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "psychologist":
        notes = (
            db.query(Note)
            .filter(Note.author_id == current_user.id, Note.kind == "psychologist_note")
            .order_by(Note.updated_at.desc())
            .all()
        )
    elif current_user.role == "client":
        notes = (
            db.query(Note)
            .filter(Note.author_id == current_user.id, Note.kind == "client_note")
            .order_by(Note.updated_at.desc())
            .all()
        )
    else:
        notes = db.query(Note).order_by(Note.updated_at.desc()).all()
    return [_serialize_note(note) for note in notes]


@router.post("/", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
def create_note(
    payload: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "psychologist":
        if not payload.client_id:
            raise HTTPException(status_code=400, detail="Для заметки психолога нужно выбрать клиента")
        client = db.get(User, payload.client_id)
        if not client or client.role != "client":
            raise HTTPException(status_code=404, detail="Клиент не найден")
        note = Note(
            author_id=current_user.id,
            client_id=client.id,
            kind="psychologist_note",
            text=payload.text,
        )
    elif current_user.role == "client":
        note = Note(
            author_id=current_user.id,
            client_id=current_user.id,
            kind="client_note",
            text=payload.text,
        )
    else:
        raise HTTPException(status_code=403, detail="Администратор не создает заметки")

    db.add(note)
    db.commit()
    db.refresh(note)
    return _serialize_note(note)


@router.put("/{note_id}", response_model=NoteRead)
def update_note(
    note_id: int,
    payload: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Заметка не найдена")
    if current_user.role != "admin" and note.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Можно редактировать только свои заметки")

    note.text = payload.text
    note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(note)
    return _serialize_note(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Заметка не найдена")
    if current_user.role != "admin" and note.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Можно удалить только свои заметки")

    db.delete(note)
    db.commit()


@router.get("/recommendations", response_model=list[RecommendationRead])
def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "client":
        recommendations = (
            db.query(Recommendation)
            .filter(Recommendation.client_id == current_user.id)
            .order_by(Recommendation.created_at.desc())
            .all()
        )
    elif current_user.role == "psychologist":
        recommendations = (
            db.query(Recommendation)
            .filter(Recommendation.psychologist_id == current_user.id)
            .order_by(Recommendation.created_at.desc())
            .all()
        )
    else:
        recommendations = db.query(Recommendation).order_by(Recommendation.created_at.desc()).all()
    return [_serialize_recommendation(recommendation) for recommendation in recommendations]


@router.post("/recommendations", response_model=RecommendationRead, status_code=status.HTTP_201_CREATED)
def create_recommendation(
    payload: RecommendationCreate,
    current_user: User = Depends(require_roles("psychologist")),
    db: Session = Depends(get_db),
):
    client = db.get(User, payload.client_id)
    if not client or client.role != "client":
        raise HTTPException(status_code=404, detail="Клиент не найден")

    recommendation = Recommendation(
        psychologist_id=current_user.id,
        client_id=client.id,
        text=payload.text,
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return _serialize_recommendation(recommendation)


@router.post("/reviews", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreate,
    current_user: User = Depends(require_roles("client")),
    db: Session = Depends(get_db),
):
    psychologist = db.get(User, payload.psychologist_id)
    if not psychologist or psychologist.role != "psychologist":
        raise HTTPException(status_code=404, detail="Психолог не найден")

    has_recommendation = (
        db.query(Recommendation)
        .filter(
            Recommendation.psychologist_id == psychologist.id,
            Recommendation.client_id == current_user.id,
        )
        .first()
        is not None
    )
    has_consultation = (
        db.query(Slot)
        .filter(
            Slot.psychologist_id == psychologist.id,
            Slot.client_id == current_user.id,
        )
        .first()
        is not None
    )
    if not (has_recommendation or has_consultation):
        raise HTTPException(
            status_code=403,
            detail="Отзыв можно оставить после рекомендации или записи к психологу",
        )

    review = (
        db.query(Review)
        .filter(
            Review.psychologist_id == psychologist.id,
            Review.client_id == current_user.id,
        )
        .first()
    )
    if review:
        review.rating = payload.rating
        review.text = payload.text
    else:
        review = Review(
            psychologist_id=psychologist.id,
            client_id=current_user.id,
            rating=payload.rating,
            text=payload.text,
        )
        db.add(review)

    db.flush()
    _recalculate_rating(db, psychologist)
    db.commit()
    db.refresh(review)
    return review
