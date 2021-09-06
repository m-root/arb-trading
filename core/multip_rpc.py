import os
import asyncio
import concurrent.futures
import contextlib
import json
import threading
import time
from typing import Any, Optional, Union

import web3
from eth_typing import URI
from web3 import HTTPProvider
from web3.providers.websocket import (
    DEFAULT_WEBSOCKET_TIMEOUT,
    PersistentWebSocket,
    WebsocketProvider,
)
from web3.types import RPCResponse, RPCEndpoint


class Multiplexer:
    @classmethod
    async def new(cls, conn: PersistentWebSocket):
        return cls(await conn.__aenter__(), asyncio.Queue())

    def __init__(self, conn, queue):
        self._conn = conn
        self._queue = queue
        self._events = {}
        self._responses = {}

    async def send(self):
        while True:
            data = await self._queue.get()
            await self._conn.send(data)

    async def recv(self):
        while True:
            data = await self._conn.recv()
            id = json.loads(data)["id"]  # TODO: error handling?
            self._responses[id] = data
            self._events.pop(id).set()

    async def run(self):
        await asyncio.gather(
            self.send(),
            self.recv(),
        )

    def __call__(self, data):
        event = threading.Event()
        id = json.loads(data)["id"]
        self._events[id] = event
        self._queue.put_nowait(data)
        event.wait()
        return self._responses.pop(id)


class MultiplexingWebsocketProvider(WebsocketProvider):
    def __init__(
        self,
        endpoint_uri: Optional[Union[URI, str]] = None,
        websocket_kwargs: Optional[Any] = None,
        websocket_timeout: int = DEFAULT_WEBSOCKET_TIMEOUT,
    ) -> None:
        super().__init__(endpoint_uri, websocket_kwargs, websocket_timeout)
        self._multiplexer = None
        self._multiplexer_fut = None

    def make_request(self, method: RPCEndpoint, params: Any) -> RPCResponse:
        request_data = self.encode_rpc_request(method, params)
        if self._multiplexer is None:
            assert self._multiplexer_fut is None
            self._multiplexer = asyncio.run_coroutine_threadsafe(
                Multiplexer.new(self.conn),
                self._loop,
            ).result()
            self._multiplexer_fut = asyncio.run_coroutine_threadsafe(
                self._multiplexer.run(),
                self._loop,
            )  # TODO: stop properly
        return json.loads(self._multiplexer(request_data))

