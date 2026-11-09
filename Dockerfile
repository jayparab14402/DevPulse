FROM python:3.14

WORKDIR /backend

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 1234

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "1234"]