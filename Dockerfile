FROM python:3.11-slim

WORKDIR /app

COPY dcbd_assign_ankush.py .

RUN pip install requests

CMD ["python", "dcbd_assign_ankush.py"]