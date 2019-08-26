# coding=utf-8
# __author__ = 'Mio'
import logging
import random
import shutil
import string
from dataclasses import dataclass
from fileinput import FileInput
from pathlib import Path
from typing import Union

import docker
import docker.errors
from docker.models.containers import Container
from docker.models.images import Image
from docker.models.networks import Network
from docker.types import Mount

from Manager.majordomo.init_house import init_maria
from Manager.model import make_session
from Manager.settings import (
    DATA_PATH_PREFIX, REVERSE_PROXY_CONTAINER_NAME, LOG_MAX_SIZE, LOG_MAX_FILE,
    COMMON_DB_CONTAINER_NAME, COMMON_DB_PW,
    client)
from Manager.model.tenant import Tenant as TenantTable
from Manager.utils import real_path

CPU1_PERIOD = 100000
CPU1_QUOTA = 100000


@dataclass
class Tenant:
    user_name: str
    user_id: int
    host: str = ''
    network_id: str = ''
    mysql_pw: str = ''
    image: Image = client.images.get('mio-wp')

    def __post_init__(self):
        # path
        self.user_path = Path(DATA_PATH_PREFIX) / str(self.user_id)
        self.wp_path = self.user_path / 'wp'
        self.db_path = self.user_path / 'db'
        # container
        self.container_name = f"{self.user_id}-wp"
        self.db_container_name = f'{self.user_id}-db'
        self.redis_container_name = f'{self.user_id}-redis'
        self.network_name = f"{self.user_id}-net"
        self.reverse_proxy_container_name = REVERSE_PROXY_CONTAINER_NAME
        # common db
        self.common_db_container_name = COMMON_DB_CONTAINER_NAME
        self.common_db_user_name = f"wpw_{self.user_id}"
        self.common_db_name_by_user = f"wpw_wp_{self.user_id}"
        self.common_db_root_pw = COMMON_DB_PW
        # container start kwargs
        self.log_config = {'config': {'max-file': LOG_MAX_FILE, 'max-size': LOG_MAX_SIZE}}

        self.update_db_record()

    def update_db_record(self):
        with make_session() as session:
            q = session.query(TenantTable).filter_by(user_id=self.user_id).first()
            if not q:
                t = TenantTable(
                    user_id=self.user_id,
                    user_name=self.user_name,
                    network_id=self.network_id,
                    mysql_pw=self.mysql_pw
                )
                session.add(t)
            else:
                q.user_name = self.user_name
                q.network_id = self.network_id
                q.mysql_pw = self.mysql_pw

    @property
    def network(self):
        return self.prepare_network()

    @property
    def mounts(self):
        return [
            Mount(
                type='bind',
                source=real_path(self.wp_path),
                target='/var/www/html'
            ),
        ]

    def prepare_network(self, force=False) -> Network:
        if not force and self.network_id:
            try:
                return client.networks.get(network_id=self.network_id)
            except (docker.errors.NotFound, docker.errors.APIError) as e:
                logging.error(e)
                print('network_id go wrong, try to get a exists or create a new one')
        # got exists network named '{self.network_name}'
        # if duplicate name networks exists, return first got, remove rest of them
        target_n = None
        duplicated = False
        for n in client.networks.list():
            if n.name == self.network_name:
                if duplicated is True:
                    try:
                        n.remove()
                    except Exception as e:
                        print(e)
                else:
                    self.network_id = n.id
                    target_n = n
                    duplicated = True
            else:
                if duplicated is True:
                    break
        # create new one
        if not target_n:
            target_n = client.networks.create(name=self.network_name)
        self.network_id = target_n.id
        # noinspection PyAttributeOutsideInit
        self.network_name = target_n.name
        self.update_db_record()
        return target_n

    @classmethod
    def cpu_limit(cls, cpus=1) -> dict:
        return dict(cpu_period=CPU1_PERIOD, cpu_quota=cpus * CPU1_QUOTA)

    def prepare_redis_container(self, **kwargs):
        container_kwargs = dict(
            image=client.images.get('redis'),
            name=self.redis_container_name,
            detach=True,
            network=self.network_name,
            log_config={'config': {'max-file': '1', 'max-size': '10m'}},
            mem_limit='100m',
            **self.cpu_limit(cpus=1),
        )
        container_kwargs.update(kwargs)
        try:
            print(f"starting {container_kwargs['name']}", end='...')
            client.containers.run(**container_kwargs)
        except Exception as e:
            print(e)
            logging.error(e)
        else:
            print('done')

    def prepare_db_container(self, **kwargs):
        container_kwargs = dict(
            image=client.images.get("mariadb"),
            name=self.db_container_name,
            detach=True,
            environment={
                'MYSQL_ROOT_PASSWORD': 'root',
                'MYSQL_DATABASE': 'wp',
            },
            network=self.network_name,
            mounts=[Mount(
                type='bind',
                source=real_path(self.db_path),
                target='/var/lib/mysql'
            )],
            log_config={'config': {'max-file': '1', 'max-size': '10m'}},
            mem_limit='100m',
            **self.cpu_limit(cpus=1),
            **kwargs,
        )
        container_kwargs.update(kwargs)
        try:
            print(f"starting {container_kwargs['name']}", end='...')
            client.containers.run(**container_kwargs)
        except Exception as e:
            print(e)
            logging.error(e)
        else:
            print('done')

    def prepare_container(self, **kwargs):
        labels = {
            "traefik.docker.network": self.network_name,
        }
        if self.host:
            labels["traefik.frontend.rule"] = f"Host:{self.host}"

        environment = {
            'WORDPRESS_DB_NAME': 'wp',
            'WORDPRESS_DB_USER': 'root',
            'WORDPRESS_DB_PASSWORD': 'root',
            'WORDPRESS_DB_HOST': self.db_container_name,
            'LISTEN_PORT': 80,
        }
        if kwargs.get('environment'):
            environment.update(kwargs['environment'])
        print(environment)
        container_kwargs = dict(
            image=self.image,
            name=self.container_name,
            detach=True,
            environment=environment,
            network=self.network_name,
            mounts=self.mounts,
            log_config=self.log_config,
            mem_limit='100m',
            labels=labels,
            **self.cpu_limit(cpus=1)
        )
        container_kwargs.update(**kwargs)
        try:
            print(f"starting {self.container_name}", end='...')
            client.containers.run(
                **container_kwargs
            )
        except Exception as e:
            print(e)
            logging.error(e)
        else:
            print('done')

    def reverse_proxy(self) -> None:
        """
        put the reverse_proxy container to user's private network
        """
        if self.reverse_proxy_container_name not in (c.name for c in self.network.containers):
            for c in client.containers.list():
                if c.name == self.reverse_proxy_container_name:
                    try:
                        self.network.connect(c)
                    except Exception as e:
                        print(e)

                    break

    def generate_pw(self, length=12):
        return ''.join(
            random.SystemRandom().choice(string.ascii_letters + '#$!+-_=><?@|{}()~' + string.digits) for _ in
            range(length))

    @property
    def common_db_container(self) -> Container:
        for c in client.containers.list():
            if c.name == self.common_db_container_name:
                db_container = c
                break
        else:
            db_container = init_maria()
        return db_container

    def prepare_common_db_user(self) -> None:
        """
        准备公共数据库的用户
        :return:
        """
        if not self.mysql_pw:
            self.mysql_pw = self.generate_pw()

        sql_create_user = f"""
        CREATE USER IF NOT EXISTS '{self.common_db_user_name}' IDENTIFIED BY '{self.mysql_pw}'
        WITH MAX_CONNECTIONS_PER_HOUR 200
        MAX_USER_CONNECTIONS 50;
        """

        sql_create_db = f"""
        CREATE DATABASE IF NOT EXISTS {self.common_db_name_by_user} CHARACTER SET=utf8mb4;
        """

        sql_grant_user = f"""
        grant Select,Insert,References,Update,Delete,Create,Drop,Index,Alter
        on {self.common_db_name_by_user}.* to {self.common_db_user_name}@'%' identified by '{self.mysql_pw}';
        """

        sql_flush_pvi = f"""flush privileges;"""

        sql = sql_create_user + sql_create_db + sql_grant_user + sql_flush_pvi
        sql = f"""mysql -uroot -p{self.common_db_root_pw} -e \"{sql}\""""

        print(self.common_db_container.exec_run(cmd=sql, demux=True))
        self.update_db_record()
        self.update_wp_config()

    def start_by_model_p(self) -> None:
        """
        MODEL S, using [private] mysql and redis
        """
        self.prepare_network()
        self.prepare_db_container()
        self.prepare_redis_container()
        self.prepare_container()
        self.reverse_proxy()

    def start_by_model_c(self) -> None:
        """
        MODEL C, using [common] mysql, and private redis
        """
        self.prepare_network()
        self.prepare_common_db_user()
        self.prepare_redis_container()
        self.prepare_container(environment={
                'WORDPRESS_DB_NAME': self.common_db_name_by_user,
                'WORDPRESS_DB_USER': self.common_db_user_name,
                'WORDPRESS_DB_PASSWORD': self.mysql_pw,
                'WORDPRESS_DB_HOST': self.common_db_container_name
            })
        self.reverse_proxy()

    @property
    def db_container(self) -> Union[Container, None]:
        try:
            return client.containers.get(self.db_container_name)
        except Exception as e:
            print(e)
            return None

    @property
    def redis_container(self) -> Union[Container, None]:
        try:
            return client.containers.get(self.redis_container_name)
        except Exception as e:
            print(e)
            return None

    @property
    def container(self) -> Union[Container, None]:
        try:
            return client.containers.get(self.container_name)
        except Exception as e:
            print(e)
            return None

    def stop(self):
        for c in (self.db_container, self.redis_container, self.container):
            if c:
                try:
                    c.stop(timeout=5)
                except Exception as e:
                    print(e.args)
                    pass

    def restart(self):
        for c in (self.db_container, self.redis_container, self.container):
            if c:
                try:
                    c.restart(timeout=5)
                except Exception as e:
                    print(e.args)
                    pass

    def remove(self):
        self.stop()
        for c in (self.db_container, self.redis_container, self.container):
            if c:
                try:
                    c.remove(v=True)
                except Exception as e:
                    print(e.args)
                    pass

    def drop_common_db_user(self):
        # drop user
        sql = f"""drop user '{self.common_db_user_name}';flush privileges;"""
        sql = f"""mysql -uroot -p{self.common_db_root_pw} -e \"{sql}\""""
        print(self.common_db_container.exec_run(cmd=sql, demux=True))
        # TODO drop db
        # modify wp-config.php

    def update_wp_config(self):
        if (self.wp_path/'wp-config.php').exists():
            with FileInput(files=self.wp_path / 'wp-config.php', inplace=True) as i:
                for ii in i:
                    # change password
                    if ii.startswith("define( 'DB_PASSWORD',"):
                        ii = f"define( 'DB_PASSWORD', '{self.mysql_pw}' );"
                        print(ii)
                    else:
                        print(ii, end='')

    def prune(self, db=False, common_db=False):
        self.remove()
        if self.wp_path.exists():
            shutil.rmtree(self.wp_path)
        if db and self.db_path.exists():
            shutil.rmtree(self.db_path)
            try:
                self.network.remove()
            except Exception as e:
                print(e)
        self.network_id = ''

        if common_db:
            self.drop_common_db_user()

        self.update_db_record()
