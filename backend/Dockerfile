# Use an official Python image that includes Playwright
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set the working directory inside the container
WORKDIR /app

#
# --- THIS IS THE FIX (Part 1: Caching) ---
# Force ALL known cache directories to the writeable /tmp folder
# This is for sentence-transformers, huggingface_hub, etc.
ENV TRANSFORMERS_CACHE=/tmp
ENV HF_HOME=/tmp
ENV HUGGINGFACE_HUB_CACHE=/tmp
ENV SENTENCE_TRANSFORMERS_HOME=/tmp
# --- END OF FIX ---
#

# Copy the requirements file first to cache dependencies
COPY requirements.txt .

# Install all your Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your backend code into the container
COPY . .

#
# --- THIS IS THE FIX (Part 2: Memory) ---
# Change '--workers 2' to '--workers 1'
# This cuts the app's startup memory usage in half.
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", "1", "backend_app:app"]
# --- END OF FIX ---