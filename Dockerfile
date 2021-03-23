# specify starting python base
FROM python:3.8-slim-buster

# name working directory
WORKDIR /app

# Copy in requirements to install
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# copy in source code
COPY . . 

# add commands for the image to execute
CMD ["python3", "test.py"]
