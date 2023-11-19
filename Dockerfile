FROM ubuntu:latest
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y python3.10-venv

RUN apt-get install git wget ca-certificates -y
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN bash -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -sc)-pgdg main" >> /etc/apt/sources.list.d/pgdg.list'
RUN apt-get update
RUN apt-get install -y postgresql

RUN git clone https://github.com/nottolstybai/DemidovCourse.git

WORKDIR /DemidovCourse

RUN python3.10 -m venv venv && \
    . venv/bin/activate && \
    pip install -r requirements.txt

RUN psql -c "ALTER USER postgres WITH PASSWORD 'postgres'"

EXPOSE 8080

CMD ["bash", "-c", "source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8080 --reload"]
