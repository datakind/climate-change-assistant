
# If you’re on Mac M1, replace the line below with "FROM --platform=linux/amd64 python:3.9-slim"
FROM python:3.10-slim

ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Copy your application's requirements and install them
COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

# Copy your application code into the container
COPY . /app/

EXPOSE 8080

CMD ["python", "-m", "chainlit", "run", "app.py", "-h", "--port", "8080"]
