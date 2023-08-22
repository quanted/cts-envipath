FROM python:3.10.12-alpine

ENV APP_USER=www-data

RUN adduser -S $APP_USER -G $APP_USER

RUN apk update && \
	apk add gcc g++ make python3-dev

COPY . /src/

WORKDIR /src

RUN pip install -r requirements.txt

RUN rm -rf \
	/root/.cache/pip \
	/usr/local/lib/python3.10/site-packages/pip \
	/usr/local/bin/pip \
	/usr/local/lib/python3.10/site-packages/pip-23.0.1.dist-info

RUN chown -R $APP_USER:$APP_USER /src

USER $APP_USER

CMD ["waitress-serve", "--port=5003", "cts_envipath_flask:app"]
