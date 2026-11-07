# TODO(M6): write the image for the API.
#
#   FROM python:3.12-slim
#   ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
#   WORKDIR /app
#   COPY requirements.txt, then RUN pip install --no-cache-dir -r requirements.txt
#       (Why copy requirements.txt BEFORE the rest of the code? Think about layer caching.)
#   COPY app ./app
#   Create a non-root user and switch to it (USER ...). Why not run as root?
#   EXPOSE 8000
#   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
#       (No --reload in production. Why?)
