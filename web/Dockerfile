FROM python:3-alpine3.10

WORKDIR /service/web

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
ENV PYTHONPATH "${PYTHONPATH}:/service/web/"
RUN chown 777 /service/web/db/project.db

CMD [ "gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app" ]