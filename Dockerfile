FROM python:3.10-slim

WORKDIR /app

# Copy root files (main.py, requirements.txt, Dockerfile,...)
COPY main.py requirements.txt ./

COPY app ./app

RUN pip install --no-cache-dir -r requirements.txt

# Expose port 
EXPOSE 5050

CMD ["python", "main.py"]
