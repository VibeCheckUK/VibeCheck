# Use an official Python image that includes Playwright
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to cache dependencies
COPY requirements.txt .

# Install all your Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your backend code into the container
COPY . .

#
# The 'RUN playwright install' line has been REMOVED.
# The base image already has the browsers installed.
#

# This command tells Render how to start your app
# It runs Gunicorn on port 10000, pointing to your Flask app
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", "2", "backend_app:app"]