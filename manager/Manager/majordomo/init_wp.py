# coding=utf-8
# __author__ = 'Mio'
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import docker
import docker.errors
from docker.models.containers import Container
from docker.models.images import Image
from docker.models.networks import Network
from docker.types import Mount

from Manager.model.tenant import TenantTable
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
    network_id: int = None
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
        self.default_network_name = f"{self.user_id}-net"
        # container start kwargs
        self.log_config = {'config': {'max-file': '1', 'max-size': '10m'}}
        self.mounts = [
            Mount(
                type='bind',
                source=real_path(self.wp_path),
                target='/var/www/html'
            ),
        ]

    @classmethod
    async def get_or_create(cls, user_id, user_name=None, network_id=None):
        m = await TenantTable.get_by_user_id(user_id)
        if m:
            return cls(user_id=m['user_id'], user_name=m['user_name'], network_id=m['network_id'])
        else:
            return cls(user_id=user_id, user_name=user_name, network_id=network_id)

    async def update_table(self):
        await TenantTable.new(user_id=self.user_id, user_name=self.user_name, network_id=self.network_id)

    async def network(self) -> Network:
        return await self.prepare_network()

    async def prepare_network(self) -> Network:
        if self.network_id:
            try:
                return client.networks.get(network_id=self.network_id)
            except (docker.errors.NotFound, docker.errors.APIError) as e:
                logging.error(e)

        n = client.networks.create(name=self.default_network_name)
        self.network_id = n.id
        await self.update_table()
        return n

    @classmethod
    def cpu_limit(cls, cpus=1) -> dict:
        return dict(cpu_period=CPU1_PERIOD, cpu_quota=cpus * CPU1_QUOTA)

    def prepare_redis_container(self):
        container_kwargs = dict(
            image=client.images.get('redis'),
            name=self.redis_container_name,
            detach=True,
            network=self.default_network_name,
            log_config={'config': {'max-file': '1', 'max-size': '10m'}},
            mem_limit='100m',
            **self.cpu_limit(cpus=1),
        )
        try:
            print(f"starting {container_kwargs['name']}")
            client.containers.run(**container_kwargs)
        except Exception as e:
            print(e)
            logging.error(e)
        else:
            print('done')

    def prepare_db_container(self):
        container_kwargs = dict(
            image=client.images.get("mariadb"),
            name=self.db_container_name,
            detach=True,
            environment={
                'MYSQL_ROOT_PASSWORD': 'root',
                'MYSQL_DATABASE': 'wp',
            },
            network=self.default_network_name,
            mounts=[Mount(
                type='bind',
                source=real_path(self.db_path),
                target='/var/lib/mysql'
            )],
            log_config={'config': {'max-file': '1', 'max-size': '10m'}},
            mem_limit='100m',
            **self.cpu_limit(cpus=1),
        )
        try:
            print(f"starting {container_kwargs['name']}")
            client.containers.run(**container_kwargs)
        except Exception as e:
            print(e)
            logging.error(e)
        else:
            print('done')

    def prepare_container(self):
        try:
            client.containers.run(
                image=self.image,
                name=self.container_name,
                detach=True,
                environment={
                    'WORDPRESS_DB_NAME': 'wp',
                    'WORDPRESS_DB_USER': 'root',
                    'WORDPRESS_DB_PASSWORD': 'root',
                    'WORDPRESS_DB_HOST': 'maria'
                },
                mounts=self.mounts,
                log_config=self.log_config,
                **self.cpu_limit(cpus=1)
            )
        except Exception as e:
            print(e)
            logging.error(e)

    def start(self):
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