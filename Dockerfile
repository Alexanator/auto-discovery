FROM /y2/alpine-node:latest

ENV TZ="Europe/Moscow"
ADD requirements.txt /tmp/requirements.txt
COPY auto-discovery.py run.sh /app/
RUN sed -i 's/http\:\/\/dl-cdn.alpinelinux.org/http\:\/\/mirror.yandex.ru\/mirrors/g' /etc/apk/repositories \
    && apk --no-cache add tzdata python3 py3-pip && pip3 install --upgrade pip && pip3 install -r /tmp/requirements.txt && rm -rf /tmp/requirements.txt \
    && chmod +x /app/run.sh && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

ENTRYPOINT [ "sh", "run.sh" ]