# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Make ports 3000 and 5000 available to the world outside this container
EXPOSE 3000 5000

# Define environment variable with a default value
ENV LOG_LEVEL=${LOG_LEVEL:-DEBUG}

# Run main.py when the container launches
CMD ["python", "src/server/main.py"]
