FROM python:3.9-alpine

RUN apk update && \
	apk add gcc g++ make python3-dev

COPY . /src/

WORKDIR /src

RUN pip install -r requirements.txt

CMD ["waitress-serve", "--port=5003", "cts_envipath_flask:app"]