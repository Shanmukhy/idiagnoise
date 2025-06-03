FROM ubuntu:20.04 as base

ENV app=Flask
EXPOSE 5000

WORKDIR /dicom-service

# Copy the content of the local src directory to the working directory
COPY . /dicom-service

### Stage 1 - add/remove packages ###
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt


# NOTE: intentionally NOT using s6 init as the entrypoint
# This would prevent container debugging if any of those service crash
CMD ["python3", "main.py"]
