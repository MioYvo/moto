# coding=utf-8
# __author__ = 'Mio'
from docker.models.containers import Container
from docker.types import Mount

from majordomo.settings import client, COMMON_DB_CONTAINER_NAME, COMMON_DB_DATA_PATH, COMMON_DB_PW
from majordomo.utils import real_path


def init_maria() -> Container:
    """
    docker run -d --name maria -v /data/mariadb:/var/lib/mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root mariadb:latest
    """
    return client.containers.run(
        image='maria', name=COMMON_DB_CONTAINER_NAME, mounts=[
            Mount(
                type='bind',
                source=real_path(COMMON_DB_DATA_PATH),
                target='/var/lib/mysql'
            ),
        ],
        environment=dict(MYSQL_ROOT_PASSWORD=COMMON_DB_PW),
        detach=True
    )


def init_pg() -> Container:
    """
    docker run --name pg -p 5432:5432 -e POSTGRES_PASSWORD=postgres -d postgres:alpine
    :return:
    """
    pass