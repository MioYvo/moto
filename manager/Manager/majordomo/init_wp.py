# coding=utf-8
# __author__ = 'Mio'
import logging
from dataclasses import dataclass
from pathlib import Path

import docker
import docker.errors
from docker.models.networks import Network
from docker.types import Mount

from Manager.settings import DATA_PATH_PREFIX

client = docker.from_env()


@dataclass
class Tenant:
    user_name: str
    user_id: int
    network_id: int

    def __post_init__(self):
        self.data_folder_name = self.user_id

        self.container_name = f"{self.user_id}-wp"

    @property
    def network(self) -> Network:
        if self.network_id:
            try:
                return client.networks.get(network_id=self.network_id)
            except (docker.errors.NotFound, docker.errors.APIError) as e:
                logging.error(e)

        return client.networks.create(name=self.user_name + str(self.user_id))

    @property
    def mount(self) -> Mount:
        return Mount(
            type='bind',
            source=Path(DATA_PATH_PREFIX) / self.data_folder_name,
            target='/var/www/html'
        )

    def prepare_redis_container(self):
        image = "redis"
        network = self.network


def wp(tenant: Tenant):
    client.containers.run()
