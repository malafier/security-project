FROM nginx:1.25

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d

RUN mkdir /etc/nginx/certs
COPY ala.key /etc/nginx/certs
COPY ala.crt /etc/nginx/certs
COPY global.pass /etc/nginx/certs
