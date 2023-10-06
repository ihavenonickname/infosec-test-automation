
import asyncio
import json
import uuid

import aiomqtt

from custom_logger import LOGGER, extra

def handle(topic):
    def create_wraper(func):
        async def wraper(payload: dict, client: aiomqtt.Client):
            trace_id = payload['trace_id']

            try:
                await client.publish('webapp/update/start', json.dumps({
                    'topic': topic,
                    'trace_id': trace_id,
                }))
            except asyncio.CancelledError:
                LOGGER.warn(
                    'Task cancelled before webapp/update/start',
                    extra=extra(trace_id, topic=topic))
                return

            error = None

            try:
                await func(payload, client)
            except asyncio.CancelledError as ex:
                LOGGER.warn(
                    'Task cancelled',
                    extra=extra(trace_id, topic=topic))
                error = str(ex)
            except Exception as ex:
                LOGGER.exception('Unhandled exception')
                error = str(ex)

            update_end_task = client.publish('webapp/update/end', json.dumps({
                'topic': topic,
                'error': error,
                'trace_id': trace_id,
            }))

            await asyncio.shield(update_end_task)

        wraper.topic = topic

        return wraper

    return create_wraper


class Fucker():
    def __init__(self, host: str, port: int, cancel_ev: asyncio.Event, handlers: list) -> None:
        self._cancel_ev = cancel_ev
        self._bg_tasks = set()
        self._client = aiomqtt.Client(host, port)
        self._handlers = handlers

    async def _handle_message(self, message: aiomqtt.Message):
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

    async def loop_forever(self):
        try:
            async with self._client:
                async with self._client.messages() as messages:
                    await self._client.subscribe('recon/#')
                    async for message in messages:
                        await self._handle_message(message)
        except Exception:
            LOGGER.exception('Unhandled exception')

        self._cancel_ev.set()
