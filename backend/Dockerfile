# Use an official Python image that includes Playwright
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set the working directory inside the container
WORKDIR /app

#
# --- THIS IS THE FIX ---
# Tell the 'sentence-transformers' library to use the writeable /tmp folder
# for its model cache, instead of the read-only default.
ENV TRANSFORMERS_CACHE=/tmp
# --- END OF FIX ---
#

# Copy the requirements file first to cache dependencies
COPY requirements.txt .

# Install all your Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your backend code into the container
COPY . .

# This command tells Render how to start your app
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", "2", "backend_app:app"]