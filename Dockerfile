FROM python:3.10-slim

# Install Java
RUN apt-get update && apt-get install -y default-jre

# Set the working directory
WORKDIR /app

# Copy your project files into the container
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the port your app runs on (optional, but good practice)
EXPOSE 10000

# Start the app with gunicorn
CMD ["gunicorn", "main:app"]
