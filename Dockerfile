# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Install Node.js and npm using apt
RUN apt-get update \
    && apt-get install -y nodejs npm

# Set the working directory to /app/node
#WORKDIR /app/node

# Install node packages THIS IS BROKEN
#COPY ./node/* /app/node/
#RUN npm install

# Set the working directory to /app
WORKDIR /app

COPY ./zdns /app/zdns

# Install Go and build zdns
RUN apt-get install -y golang-go && apt-get clean

# build go in zdns
RUN cd /app/zdns
RUN cd /app/zdns && \
    go build -buildvcs=false && \
    cd /

# Copy the current directory contents into the container at /app
COPY requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define environment variable
ENV NUM_THREADS 1

# This is stupid, I know
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
COPY *.py /app/

# Make sure the script is executable
RUN chmod +x /app/docker-entrypoint.sh

# Run docker-entrypoint.sh when the container launches
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["SEARCH"]