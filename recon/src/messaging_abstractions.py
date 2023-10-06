
import asyncio
import json
from typing import Callable, Protocol
import uuid

import aiomqtt

from custom_logger import LOGGER, extra
from helper import extract_trace_id


class MessageHandler(Protocol):
    async def __call__(self,
                       payload: dict[str, object],
                       client: aiomqtt.Client) -> None:
        ...


class MessageHandlerWraper():
    topic: str

    def __init__(self, topic: str, func: MessageHandler) -> None:
        self._original_func = func
        self.topic = topic

    async def __call__(self,
                       payload: dict[str, object],
                       client: aiomqtt.Client) -> None:
        trace_id: str = extract_trace_id(payload)

        try:
            await client.publish('webapp/update/start', json.dumps({
                'topic': self.topic,
                'trace_id': trace_id,
            }))
        except asyncio.CancelledError:
            LOGGER.warn(
                'Task cancelled before webapp/update/start',
                extra=extra(trace_id, topic=self.topic))
            return

        error = None

        try:
            await self._original_func(payload, client)
        except asyncio.CancelledError as ex:
            LOGGER.warn(
                'Task cancelled',
                extra=extra(trace_id, topic=self.topic))
            error = str(ex)
        except Exception as ex:
            LOGGER.exception('Unhandled exception')
            error = str(ex)

        update_end_task = client.publish('webapp/update/end', json.dumps({
            'topic': self.topic,
            'error': error,
            'trace_id': trace_id,
        }))

        await asyncio.shield(update_end_task)


class MessagingServer():
    def __init__(self,
                 host: str,
                 port: int,
                 cancel_ev: asyncio.Event,
                 handlers: list[MessageHandlerWraper]) -> None:
        self._cancel_ev = cancel_ev
        self._bg_tasks: set[asyncio.Task[None]] = set()
        self._client = aiomqtt.Client(host, port)
        self._handlers = handlers

    async def _handle_message(self, message: aiomqtt.Message) -> None:
        if type(message.payload) != str and type(message.payload) != bytes:
            LOGGER.warn(
                'Payload must be str',
                extra={'topic': message.topic})
            return

        payload = json.loads(message.payload)

        if message.topic.matches('recon/start-pipeline'):
            trace_id = str(uuid.uuid4())

            LOGGER.debug(
                'Starting pipeline',
                extra=extra(trace_id, domain=payload['domain']))

            payload['trace_id'] = trace_id
            payload = json.dumps(payload)

            await self._client.publish('recon/subdomain-enumeration', payload)
            await self._client.publish('recon/dns-scan', payload)
        else:
            for handler in self._handlers:
                if message.topic.matches(handler.topic):
                    coro = handler(payload, self._client)
                    task = asyncio.create_task(coro)
                    self._bg_tasks.add(task)
                    task.add_done_callback(self._bg_tasks.remove)

    async def loop_forever(self) -> None:
        try:
            async with self._client:
                async with self._client.messages() as messages:
                    await self._client.subscribe('recon/#')
                    async for message in messages:
                        await self._handle_message(message)
        except Exception:
            LOGGER.exception('Unhandled exception')

        self._cancel_ev.set()


def handle(topic: str) -> Callable[[MessageHandler], MessageHandlerWraper]:
    def create_wraper(func: MessageHandler) -> MessageHandlerWraper:
        return MessageHandlerWraper(topic, func)

    return create_wraper
