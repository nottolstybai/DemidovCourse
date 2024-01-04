FROM python:3.10.13-bullseye

ENV DB_HOST=localhost

RUN apt-get update && apt-get install -y postgresql

COPY . /app

WORKDIR /app

RUN pip install --upgrade pip

RUN pip install --upgrade setuptools

RUN pip install -r requirements.txt

USER postgres

CMD ["bash", "-c", "service postgresql start && psql -U postgres -c \"ALTER USER postgres WITH PASSWORD 'postgres'\" && uvicorn main:app --host 0.0.0.0 --port 8080"]
