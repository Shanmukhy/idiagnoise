FROM ubuntu:20.04 as base

ENV app=Flask
EXPOSE 6000

RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN echo 'tzdata tzdata/Areas select Asia' | debconf-set-selectionsecho 'tzdata tzdata/Zones/Asia select Kolkata' | debconf-set-selections
RUN DEBIAN_FRONTEND="noninteractive" apt install -y tzdata
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install flask requests pillow opencv-python==4.5.1.48 pydicom PyYAML==6.0.1 APScheduler==3.10.4
RUN python3 -m pip install reportlab
RUN python3 -m pip install Flask-JWT-Extended pymongo Werkzeug
COPY ./ /

CMD ["python3", "rest_interface.py"]
