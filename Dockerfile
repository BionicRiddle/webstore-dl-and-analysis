# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

COPY ./zdns /app/zdns

# Install Go and build zdns
RUN apt-get update && \
    apt-get install -y golang-go

# build go in zdns
RUN cd /app/zdns
RUN cd /app/zdns && \
    go build && \
    cd /


# Copy the current directory contents into the container at /app
COPY requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define environment variable
ENV NUM_THREADS 4

# Run main.py when the container launches
CMD ["python", "-u", "./search.py", "/app/extensions/"]
