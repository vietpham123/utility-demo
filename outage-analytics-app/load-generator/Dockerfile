FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8089
CMD ["locust", "-f", "locustfile.py", "--headless", "--host", "http://reverse-proxy", "-u", "5", "-r", "1", "--run-time", "0"]
