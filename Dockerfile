# Use an official Python runtime as a parent image
FROM python:3.11-slim

# install go
RUN apt-get update && apt-get install -y golang-go

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define environment variable
ENV NUM_THREADS 4

# Run main.py when the container launches
CMD ["python", "-u", "./search.py", "/app/extensions/"]
