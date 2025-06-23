FROM python:3.10-slim

# Set working directory inside container (ở đây là /app)
WORKDIR /app

# Copy root files (main.py, requirements.txt, Dockerfile,...)
COPY main.py requirements.txt ./

# Copy thư mục app/ vào /app/app
COPY app ./app

# Cài dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (theo app bạn)
EXPOSE 5050

# Chạy main.py (đang ở /app)
CMD ["python", "main.py"]
