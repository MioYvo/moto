FROM python:slim

ENV TZ America/Los_Angeles
ADD . /manager
WORKDIR /manager/
RUN sed -i "s/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g" /etc/apt/sources.list \
    && set -x \
    && apt update && apt install -y gcc \
    && pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt \
    && apt autoremove -y gcc

CMD ["python", "manager.py"]
