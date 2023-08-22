FROM python:3.10.12-alpine

ENV APP_USER=www-data

RUN adduser -S $APP_USER -G $APP_USER

RUN apk update && \
	apk add gcc g++ make python3-dev

COPY . /src/

WORKDIR /src

RUN pip install -r requirements.txt

RUN chown -R $APP_USER:$APP_USER /src

USER $APP_USER

CMD ["waitress-serve", "--port=5003", "cts_envipath_flask:app"]
