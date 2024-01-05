FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10
RUN apt-get update -y

ENV PYTHONUNBUFFERED 1
ENV DB_HOST=db-service

RUN apt-get update && apt-get install -y vim
COPY . /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt

CMD ["bash", "-c", "uvicorn main:app --host 0.0.0.0 --port 8080"]