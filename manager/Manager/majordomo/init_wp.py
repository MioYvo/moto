# coding=utf-8
# __author__ = 'Mio'
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import docker
import docker.errors
from docker.models.containers import Container
from docker.models.images import Image
from docker.models.networks import Network
from docker.types import Mount

from Manager.settings import DATA_PATH_PREFIX

client = docker.from_env()

CPU1_PERIOD = 100000
CPU1_QUOTA = 100000


def real_path(p: Path) -> str:
    if not p.exists():
        p.mkdir(parents=True)
    return str(p.absolute())


@dataclass
class Tenant:
    user_name: str
    user_id: int
    network_id: str = ''
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
        # container start kwargs
        self.log_config = {'config': {'max-file': '1', 'max-size': '10m'}}

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
            self.network_name = target_n.name
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
        container_kwargs = dict(
            image=self.image,
            name=self.container_name,
            detach=True,
            environment={
                'WORDPRESS_DB_NAME': 'wp',
                'WORDPRESS_DB_USER': 'root',
                'WORDPRESS_DB_PASSWORD': 'root',
                'WORDPRESS_DB_HOST': self.db_container_name
            },
            network=self.network_name,
            mounts=self.mounts,
            log_config=self.log_config,
            mem_limit='100m',
            labels={"traefik.frontend.rule": "Host:", "traefik.docker.network": self.network_name},
            **self.cpu_limit(cpus=1)
        )
        container_kwargs.update(**kwargs)
        try:
            print(f"starting {self.container_name}", end='...')
            client.containers.run(
                **container_kwargs
            )
            self.reverse_proxy()
        except Exception as e:
            print(e)
            logging.error(e)
        else:
            print('done')

    def reverse_proxy(self):
        for c in client.containers.list():
            if c.name == "traefik_reverse-proxy_1":
                self.network.connect(c)

    def start(self):
        self.prepare_network()
        self.prepare_db_container()
        self.prepare_redis_container()
        self.prepare_container()

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

    def prune(self, db=False):
        self.remove()
        if self.wp_path.exists():
            shutil.rmtree(self.wp_path)
        if db and self.db_path.exists():
            shutil.rmtree(self.db_path)
        self.network.remove()
        self.network_id = ''
