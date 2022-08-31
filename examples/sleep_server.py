from time import sleep

import pulsar

from sleep_model import SleepRequest, SleepResponse
from src import PulsarRpcServer


class SleepPulsarRpcServer(PulsarRpcServer[SleepRequest, SleepResponse]):
    def process(self, request: SleepRequest) -> SleepResponse:
        sleep(request.time)

        return SleepResponse(
            status=1,
            message=f"Server slept for {request.time}"
        )


client = pulsar.Client('pulsar://localhost:6650')
SleepPulsarRpcServer(topic_name="example_sleep", client=client).start_listen()
