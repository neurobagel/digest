FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./digest /code/digest
COPY ./schemas /code/schemas

CMD ["gunicorn", "digest.app:server", "-b", "0.0.0.0:8050", "--workers", "4", "--threads", "2"]
