FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy source code
COPY ./app /app

COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 4000

CMD ["python", "main.py"]
