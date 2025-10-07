# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install system dependencies required for music playback
# - ffmpeg is for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
COPY . .

# Expose the port the web server will run on
EXPOSE 8080

# Make the start script executable
RUN chmod +x /app/start.sh

# Set the command to run the start script
CMD ["/app/start.sh"]