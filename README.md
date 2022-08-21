# pypulsar-rpc
Python library for RPC over Apache Pulsar

## Usage example

Service sleeps for some given timeout provided by client application and returns a message back


### Request Model
```python
from pydantic import BaseModel

class SleepRequest(BaseModel):
    time: int
```

### Response Model
```python
from pydantic import BaseModel

class SleepResponse(BaseModel):
    status: int
    message: str
```

### Server
```python
from time import sleep

import pulsar

from examples.model import SleepRequest, SleepResponse
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
```

### Client
```Python
import time
from random import randint

import pulsar

from examples.model import SleepResponse, SleepRequest
from src import PulsarRpcClient, RpcCallTimeout


class SleepPulsarRpcClient(PulsarRpcClient[SleepRequest, SleepResponse]):
    pass


client = pulsar.Client('pulsar://localhost:6650')
rpc_client = SleepPulsarRpcClient(topic_name="example_sleep", client=client)


for i in range(0, 10):
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

```
