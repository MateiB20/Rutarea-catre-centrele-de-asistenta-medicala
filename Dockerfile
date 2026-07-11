FROM python:3.12-slim


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x runmap.sh

RUN apt-get update && apt-get install -y dos2unix

RUN dos2unix runmap.sh

CMD ["./runmap.sh"]