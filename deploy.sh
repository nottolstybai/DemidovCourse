#/bin/bash

sudo apt update
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt install python3.10 -y
sudo apt install python3.10-venv -y
python3.10 --version

git clone https://github.com/nottolstybai/DemidovCourse.git

# Установка PostgreSQL 14
sudo apt-get install wget ca-certificates
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -sc)-pgdg main" >> /etc/apt/sources.list.d/pgdg.list'
sudo apt-get update
sudo apt-get install postgresql -y
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres'"

# activate venv
bash -c "cd DemidovCourse && python3.10 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8080 --reload"