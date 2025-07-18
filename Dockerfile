FROM python:alpine
WORKDIR /root
COPY . .
RUN --mount=type=cache,target=/root/.cache/pip pip install  .
RUN rm -rf *
RUN apk add ffmpeg
