FROM python:3.12
WORKDIR /app
COPY . .
RUN pip install flask pymongo requests pytest pytest-order
EXPOSE 5000
CMD ["python", "main.py"]