import logging
import uuid
import time

import pulsar

from typing import TypeVar, Generic
from abc import abstractmethod, ABCMeta
from pydantic import BaseModel
from .model import RpcRequest, RpcResponse

TRequest = TypeVar('TRequest', bound=BaseModel)
TResponse = TypeVar('TResponse', bound=BaseModel)

logger = logging.getLogger(__name__)


class PulsarRpcServer(Generic[TRequest, TResponse], metaclass=ABCMeta):
    def __init__(self,
                 topic_name: str,
                 client: pulsar.Client,
                 tenant: str = "public",
                 namespace: str = "default",
                 persistant: bool = False):

        persistance = 'persistent' if persistant else 'non-persistent'
        self.__server_id = f"{uuid.uuid4()}"
        self.__client = client
        self.__subscription = client.subscribe(f"{persistance}://{tenant}/{namespace}/{topic_name}",
                                               "subscription")

    def start_listen(self):
        while True:
            message = self.__subscription.receive()
            self.__subscription.acknowledge(message)
            request: RpcRequest = RpcRequest.parse_raw(message.data().decode("utf-8"))

            start_time = time.time()

            # pylint: disable=no-member
            model: TRequest = self.__orig_bases__[0].__args__[0].parse_raw(request.message)
            result: BaseModel = self.process(model)
            duration = (time.time() - start_time)

            logger.debug(f"RPCServer: {self.__server_id}. Procesed message from client {request.client_id} in {duration}")

            self.__client.create_producer(request.callback_topic).send(RpcResponse(
                correlation_id=request.correlation_id,
                message=result.json(),
                client_id=request.client_id,
                server_id=self.__server_id,
                duration=duration
            ).json().encode("utf-8"))

    @abstractmethod
    def process(self, request: TRequest) -> TResponse:
        pass
