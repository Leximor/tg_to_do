FROM python:3.11
RUN apt-get update && apt-get install -y curl
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . /app/
ENV API_URL=http://backend:8000/api/
ENV BOT_TOKEN='your_token'
CMD ["python", "main.py"]
