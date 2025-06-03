FROM nvcr.io/nvidia/tensorflow:22.01-tf2-py3  as base

ENV app=Flask
EXPOSE 7000
### Stage 1 - add/remove packages ###
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN echo 'tzdata tzdata/Areas select Asia' | debconf-set-selectionsecho 'tzdata tzdata/Zones/Asia select Kolkata' | debconf-set-selections
RUN DEBIAN_FRONTEND="noninteractive" apt install -y tzdata
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install flask requests pillow opencv-python==4.5.1.48 pydicom wget PyYAML==6.0.1
<<<<<<< inference/Dockerfile
RUN python3 -m pip install azure-storage-blob azure-identity pymongo
RUN python3 -m pip install Flask-JWT-Extended 
=======
RUN python3 -m pip install azure-storage-blob azure-identity pymongo flask_jwt_extended
>>>>>>> inference/Dockerfile
COPY ./ /
WORKDIR /
# NOTE: intentionally NOT using s6 init as the entrypoint
# This would prevent container debugging if any of those service crash
ENTRYPOINT ["python3", "/inference.py"]
