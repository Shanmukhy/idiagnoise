#FROM python:3.6
FROM nvcr.io/nvidia/tensorflow:22.01-tf2-py3  as base
ENV app=Flask
EXPOSE 8050
 
# Upgrade pip and install dependencies
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN echo 'tzdata tzdata/Areas select Asia' | debconf-set-selectionsecho 'tzdata tzdata/Zones/Asia select Kolkata' | debconf-set-selections
RUN DEBIAN_FRONTEND="noninteractive" apt install -y tzdata
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install flask
RUN python3 -m pip install azure-storage-blob azure-identity
RUN python3 -m pip install wget


WORKDIR /
# COPY requirements.txt /
# COPY train_resnet50.py /
COPY ./ /
RUN pip install -r requirements.txt

# Set the entry point to execute the Dummy_Dataset.py script
ENTRYPOINT [ "python3" ,"train.py"]
