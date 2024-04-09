# FROM python:3.10.12-alpine
FROM mambaorg/micromamba:1.5.8-alpine3.19

ENV APP_USER=www-data
ENV CONDA_ENV="pyenv"

USER root

RUN adduser -S $APP_USER -G $APP_USER

RUN apk update && \
	apk add gcc g++ make python3-dev

COPY . /src/

WORKDIR /src

USER $APP_USER

# RUN pip install -r requirements.txt
RUN micromamba create -n $CONDA_ENV -c conda-forge python=3.10
RUN micromamba install -n $CONDA_ENV -f /src/environment.yml
RUN micromamba clean -p -t -l --trash -y

# RUN rm -rf \
# 	/root/.cache/pip \
# 	/usr/local/lib/python3.10/site-packages/pip \
# 	/usr/local/bin/pip \
# 	/usr/local/lib/python3.10/site-packages/pip-23.0.1.dist-info

USER root

# # Security Issues Mitigations
# # ------------------------- #
# # # RUN apk del gfortran
# # RUN rm -R /opt/conda/pkgs/redis*
# # #RUN rm -R /opt/conda/bin/redis*
# # RUN rm -R /opt/conda/pkgs/postgres*
# # #RUN rm -R /opt/conda/bin/postgres*
# RUN find /opt/conda/pkgs/future* -name "*.pem" -delete || true
# RUN find /opt/conda/lib/python3.10/site-packages/future -name "*.pem" -delete || true
# RUN find /opt/conda/envs/pyenv -name "*.pem" -delete || true
# RUN find /opt/conda -name "*test.key" -delete || true
# RUN find /opt/conda/ -name 'test.key' -delete || true
# RUN find /opt/conda/ -name 'localhost.key' -delete || true
# RUN find /opt/conda/ -name 'server.pem' -delete || true
# RUN find /opt/conda/ -name 'client.pem' -delete || true
# RUN find /opt/conda/ -name 'password_protected.pem' -delete || true
# # ------------------------- #


RUN chown -R $APP_USER:$APP_USER /src

USER $APP_USER

ENV START_COMMAND="micromamba run -n $CONDA_ENV waitress-serve --port=5003 cts_envipath_flask:app"
CMD ${START_COMMAND}
# CMD ["waitress-serve", "--port=5003", "cts_envipath_flask:app"]
