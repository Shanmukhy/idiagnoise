FROM ubuntu:20.04 as base

ENV app=Flask
EXPOSE 9000


### Stage 1 - add/remove packages ###
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install pydicom==2.4.3 flask==3.0.0 Pillow==10.1.0 numpy spacy==3.7.2 PyYAML==6.0.1
RUN python3 -m spacy download en_core_web_sm

WORKDIR /
COPY ./ /
# NOTE: intentionally NOT using s6 init as the entrypoint
# This would prevent container debugging if any of those service crash
CMD ["python3", "main.py"]
