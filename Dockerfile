FROM python:3.10

# Create parent directory to have a place to mount pre-loaded digest files (currently the nipoppy-qpn repo)
# TODO: Revisit this with longer-term solution to handle available digests (e.g., QPN as submodule?)
WORKDIR /app/code

COPY ./requirements.txt /app/code/requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /app/code/requirements.txt

COPY ./digest /app/code/digest
COPY ./schemas /app/code/schemas

CMD ["gunicorn", "digest.app:server", "-b", "0.0.0.0:8050", "--workers", "4", "--threads", "2"]
