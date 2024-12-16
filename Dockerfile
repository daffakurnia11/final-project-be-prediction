# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files
# and to ensure that output is sent straight to the terminal (i.e. not buffered)
ENV PYTHONUNBUFFERED 1

# Create and set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your Django project into the container
COPY . /app/

# Expose the port the app will run on
EXPOSE 8080

# Start the Django development server (adjust the command if you're using Gunicorn in production)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
