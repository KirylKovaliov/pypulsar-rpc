import uuid
from abc import ABC, ABCMeta

import pulsar
from typing import TypeVar, Generic

from pydantic import BaseModel

from src.exceptions import RpcCallTimeout
from src.model import RpcRequest, RpcResponse

TRequest = TypeVar('TRequest', bound=BaseModel)
TResponse = TypeVar('TResponse', bound=BaseModel)


class PulsarRpcClient(Generic[TRequest, TResponse], metaclass=ABCMeta):
    def __init__(self,
                 topic_name: str,
                 client: pulsar.Client,
                 tenant: str = "public",
                 namespace: str = "default",
                 persistant: bool = False):

        self.__client_id = f"{uuid.uuid4()}"
        self.__topic_name = topic_name

        persistance = 'persistent' if persistant else 'non-persistent'

        # request
        self.__publisher = client.create_producer(f"{persistance}://{tenant}/{namespace}/{topic_name}")
        self.__callback_topic_name = f"{persistance}://{tenant}/{namespace}/{topic_name}-callback-{self.__client_id}"

        # response
        self.__callback = client.create_producer(self.__callback_topic_name)
        self.__callback_subscription = client.subscribe(self.__callback_topic_name,
                                                        "subscription",
                                                        consumer_type=pulsar.ConsumerType.Exclusive)

    def process(self, request: TRequest, timeout_ms=60000) -> TResponse:
        rpc_response = self.__execute(request.json(), timeout_ms)
        # pylint: disable=no-member

        return self.__orig_bases__[0].__args__[1].parse_raw(rpc_response.message)

    def __execute(self, message: str, timeout_ms: int) -> RpcResponse:
        correlation_id = f"{uuid.uuid4()}"

        request = RpcRequest(
            client_id=self.__client_id,
            message=message,
            correlation_id=correlation_id,
            callback_topic=self.__callback_topic_name)

        self.__publisher.send(request.json().encode("utf-8"))

        while True:
            try:
                message = self.__callback_subscription.receive(timeout_millis=timeout_ms)
                response: RpcResponse = RpcResponse.parse_raw(message.data().decode("utf-8"))
                self.__callback_subscription.acknowledge(message)

                # this is a special check to make sure that message correlation belongs to the current scope
                # there is a chance that message can stuck in a queue due to timeout
                # we would like to remove such messages *possibly with negative acknowledgement
                if response.correlation_id == correlation_id:
                    print(f"RPCClient: <{self.__client_id}>. Processing time: {response.duration}")
                    return response

            except pulsar.Timeout:
                raise RpcCallTimeout(f"RPCTimeout {timeout_ms}ms. Topic: {self.__topic_name}")

