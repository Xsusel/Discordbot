# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
COPY . .

# Expose the port the web server will run on
EXPOSE 8080

# Make the start script executable
RUN chmod +x /app/start.sh

# Set the command to run the start script
CMD ["/app/start.sh"]