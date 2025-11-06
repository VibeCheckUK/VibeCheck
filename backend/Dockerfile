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

# Run the Playwright installer to get the browsers
RUN playwright install --with-deps chromium

# This command tells Render how to start your app
# It runs Gunicorn on port 10000, pointing to your Flask app
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", "2", "backend_app:app"]