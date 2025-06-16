FROM python:3.10-slim

# Install Java and other dependencies
RUN apt-get update && apt-get install -y default-jre git && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy your project files into the container
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the port your app runs on (change if needed)
EXPOSE 10000

# Start the app with gunicorn
CMD gunicorn --bind 0.0.0.0:${PORT:-10000} main:app
