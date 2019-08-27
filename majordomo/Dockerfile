FROM python:alpine

ENV TZ America/Los_Angeles
ADD . /majordomo
WORKDIR /majordomo/
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories \
    && set -x \

    && apk add --no-cache --virtual .build-deps \
                gcc \
                g++ \
                make \
                openssl-dev \
                libffi-dev \
                postgresql-dev \
            && pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt \
            && apk del .build-deps \
            && apk add --no-cache libpq

CMD ["python", "manager.py"]
