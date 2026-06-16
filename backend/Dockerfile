# FROM python:3.11

# WORKDIR /app

# COPY requirements.txt .
# RUN pip install -r requirements.txt

# COPY . .

# CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

# FROM python:3.11

# WORKDIR /app

# COPY requirements.txt .
# RUN pip install -r requirements.txt

# COPY . . 

# # Переменные по умолчанию (можно переопределить при запуске)
# ENV DATABASE_URL=postgresql://postgres:postgres@db:5432/psychology
# ENV JWT_SECRET=development-secret-change-me
# ENV CORS_ORIGINS=http://localhost:5173
# ENV ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV DATABASE_URL=postgresql://postgres1:1d7diUVaHy5F5wW2iyrE4tB5DqUp78UH@dpg-d8oroa0k1i2s73ekuidg-a/psychology_qxo6
ENV JWT_SECRET=development-secret-change-me
ENV CORS_ORIGINS=http://localhost:5173
ENV ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENV LOG_LEVEL=INFO


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
