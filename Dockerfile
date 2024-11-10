# Dockerfile

FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the application files into the container
COPY . .

# Install Flask and requests for HTTP communication
RUN pip install --no-cache-dir flask requests

# Expose port 5000
EXPOSE 5000

# Run the Flask application
CMD ["flask", "run"]
