
import asyncio
import json
import traceback

import aiomqtt

from log import LOGGER, extra

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
                error = str(ex)
                stacktrace = '\n'.join(
                    traceback.format_tb(ex.__traceback__))
                LOGGER.error(
                    'Unhandled exception',
                    extra=extra(
                        trace_id,
                        topic=topic,
                        type=type(ex).__name__,
                        exc_message=error,
                        exc_stacktrace=stacktrace))

            update_end_task = client.publish('webapp/update/end', json.dumps({
                'topic': topic,
                'error': error,
                'trace_id': trace_id,
            }))

            await asyncio.shield(update_end_task)

        wraper.topic = topic

        return wraper

    return create_wraper
