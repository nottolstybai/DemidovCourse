FROM python:3.10.13-bullseye

RUN apt-get install git -y

RUN git clone https://github.com/nottolstybai/DemidovCourse.git

WORKDIR /DemidovCourse

RUN pip install -r requirements.txt
