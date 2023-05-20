FROM python:3.10

EXPOSE 8000

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY src/ ./

ENTRYPOINT [ "python", "./main.py" ]