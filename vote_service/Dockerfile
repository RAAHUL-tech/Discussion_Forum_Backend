FROM python:3.8-slim

WORKDIR /app

COPY . /app
RUN pip install -r requirements.txt

EXPOSE 5003

CMD ["python", "app.py"]
