from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Note, Recommendation, Slot, User
from app.security import hash_password


def seed_database(db: Session) -> None:
    if db.query(User).count() > 0:
        return

    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password=hash_password("admin123"),
        role="admin",
    )
    psychologist = User(
        username="psy_maria",
        email="maria@example.com",
        hashed_password=hash_password("psych123"),
        role="psychologist",
        full_name="Мария Иванова",
        specialization="Тревожность, стресс, семейные консультации",
        education="МГУ, факультет психологии. КПТ, семейная терапия.",
        rating=4.8,
        rating_count=12,
    )
    psychologist_two = User(
        username="psy_anna",
        email="anna@example.com",
        hashed_password=hash_password("psych123"),
        role="psychologist",
        full_name="Анна Петрова",
        specialization="Самооценка, эмоциональное выгорание",
        education="СПбГУ, клиническая психология. Гештальт-терапия.",
        rating=4.6,
        rating_count=8,
    )
    client = User(
        username="client_lena",
        email="lena@example.com",
        hashed_password=hash_password("client123"),
        role="client",
        specialization="Хочу разобраться со стрессом на работе",
        about="Предпочитаю сохранять анонимность.",
    )
    client_two = User(
        username="client_ivan",
        email="ivan@example.com",
        hashed_password=hash_password("client123"),
        role="client",
        specialization="Интересует работа с тревожностью",
    )

    db.add_all([admin, psychologist, psychologist_two, client, client_two])
    db.flush()

    base_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
    slots = [
        Slot(
            psychologist_id=psychologist.id,
            start_at=base_time,
            end_at=base_time + timedelta(hours=1),
            specialization="Индивидуальная консультация",
            meeting_link="https://meet.example.com/maria-1",
        ),
        Slot(
            psychologist_id=psychologist.id,
            client_id=client.id,
            start_at=base_time + timedelta(hours=2),
            end_at=base_time + timedelta(hours=3),
            specialization="КПТ-консультация",
            meeting_link="https://meet.example.com/maria-2",
        ),
        Slot(
            psychologist_id=psychologist_two.id,
            start_at=base_time + timedelta(days=1),
            end_at=base_time + timedelta(days=1, hours=1),
            specialization="Выгорание и восстановление",
            meeting_link="https://meet.example.com/anna-1",
        ),
    ]
    db.add_all(slots)
    db.flush()

    db.add_all(
        [
            Recommendation(
                psychologist_id=psychologist.id,
                client_id=client.id,
                text="Попробуйте короткую дыхательную практику 4-7-8 перед сном и фиксируйте уровень напряжения утром.",
            ),
            Note(
                author_id=psychologist.id,
                client_id=client.id,
                kind="psychologist_note",
                text="Клиент отмечает рост тревожности в рабочих ситуациях. Обсудить автоматические мысли.",
            ),
            Note(
                author_id=client.id,
                client_id=client.id,
                kind="client_note",
                text="После прогулки стало легче. Стоит повторить завтра.",
            ),
        ]
    )

    db.commit()
