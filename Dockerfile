# Use the lightweight and secure Alpine image as the base.
FROM python:3.13.3-alpine

# Set environment variables to prevent Python from writing .pyc files
# and to ensure output is sent straight to the container logs.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build-time dependencies needed for some Python packages on Alpine.
# We will remove them in the same layer to keep the final image clean.
RUN apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev

# Set the working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Remove the build-time dependencies
RUN apk del .build-deps

# Install the PostgreSQL client tools needed for the start.sh script
RUN apk add --no-cache postgresql-client redis

# Copy the rest of the application code
COPY . .

# Make the startup script executable (using the correct absolute path)
RUN chmod +x /app/start.sh

# Set a non-root user for better security
RUN addgroup -S app && adduser -S -G app app
USER app

# Expose the port that Gunicorn will run on.
EXPOSE 5000



# The command to run the application (using the correct absolute path)
CMD ["/app/start.sh"]