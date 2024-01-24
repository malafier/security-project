FROM python:3-alpine3.10

WORKDIR /service

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY web/requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN chown 777 /service/web/db/project.db

#WORKDIR /web
#ENTRYPOINT ["python3"]
#CMD ["app.py"]
CMD [ "gunicorn", "--bind", "0.0.0.0:5000", "web.wsgi:app" ]