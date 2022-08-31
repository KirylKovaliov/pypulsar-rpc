import time
from random import randint

import pulsar

from examples.sleep_model import SleepResponse, SleepRequest
from src import PulsarRpcClient, RpcCallTimeout

class SleepPulsarRpcClient(PulsarRpcClient[SleepRequest, SleepResponse]):
    pass


client = pulsar.Client('pulsar://localhost:6650')
rpc_client = SleepPulsarRpcClient(topic_name="example_sleep", client=client)

for i in range(0, 50000):
    start_time = time.time()
    sleep_for = randint(0, 2)

    try:
        result = rpc_client.process(
            SleepRequest(time=sleep_for),
            timeout_ms=6 * 1000          # 6 seconds timeout
        )
        print(f"--- Result: {result.message}. Processing time: {(time.time() - start_time)} ---")
    except RpcCallTimeout:
        print(f"--- Result: timeout. Sleep For: {sleep_for}")


