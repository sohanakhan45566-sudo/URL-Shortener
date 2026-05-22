FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install flask pymongo python-dotenv
COPY app.py .
CMD ["python", "app.py"]