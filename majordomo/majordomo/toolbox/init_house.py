# coding=utf-8
# __author__ = 'Mio'
from docker.models.containers import Container
from docker.types import Mount

from majordomo.model import Base
from majordomo.settings import client, COMMON_DB_CONTAINER_NAME, COMMON_DB_DATA_PATH, COMMON_DB_PW, engine
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
    docker run --name pg -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=moto -d postgres:alpine
    :return:
    """
    Base.metadata.create_all(engine)
    pass


def init_traefik() -> Container:
    """
    docker network create traefik

    docker run -d --rm --name traefik --network traefik --publish 80:80 --publish 443:443 --publish 8000:8080 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    traefik \
    --entryPoints="Name:http Address::80" \
    --entryPoints="Name:https Address::443 TLS" \
    --api --docker --docker.endpoint="unix:///var/run/docker.sock" --loglevel=debug \
    --acme=true --acme.entrypoint=https --acme.httpchallenge --acme.httpchallenge.entrypoint=http \
    --acme.storage=/tmp/acme.json
    """
    pass


def init_data_dir():
    """
    mkdir /data
    sudo chown -hR user:user_group /data
    """
    pass


def pull_images():
    """
    docker pull redis
    docker pull postgres:alpine
    docker pull mariadb
    docker pull traefik
    """
    pass


def init_sample_wp():
    """
    docker run -it --rm --volumes-from wp-1 --network net-1 wordpress:cli \
     wp core install --url=HostUrl --title="My Blog" \
     --admin_user=admin \
     --admin_password=admin --admin_email=info@example.com

    https://developer.wordpress.org/cli/commands/core/install/
    :return:
    """
    pass


def install_plugin_in_wp():
    """
    docker run -it --rm --volumes-from wp-1 --network net-1 wordpress:cli \
     wp plugin deactivate --all ;\
     wp plugin delete --all ;\
     wp plugin install wp-fastest-cache
    :return:
    """
    pass


def migrate_sql():
    """
    # TODO use volume bind to host data path
    docker cp mfpadsupport_2019-08-19.sql maria:/
    # import sql to uses's db
    docker exec -it --rm MariaDBContainerName mysql -uDBUserName -pDBUserPassword UsersDBName < UsersMigrate.sql
    # TODO copy migrate files to /data/wp/{id}/src
    cp -r /data/{id}/src/UseNamedDir/wp-content /data/{1}/wp/.
    # change owner or "wp plugin install xx.zip" will not permmit
    cchown -R 82:82 /data/1/wp/*
    :return:
    """
    pass
