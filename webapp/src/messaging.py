import json
import aiomqtt
from database import Database


class MessagingApi():
    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port

    async def loop_forever(self, db: Database) -> None:
        try:
            async with aiomqtt.Client(self._host, self._port) as client:
                async with client.messages() as messages:
                    await client.subscribe('webapp/pipeline/step/start')
                    await client.subscribe('webapp/pipeline/step/end')
                    await client.subscribe('webapp/pipeline/start')
                    async for message in messages:
                        await self._handle_message(message, db)
        except Exception as ex:
            print('ERROR')
            print('Exiting loop_forever')
            print(ex)

    async def send_pipeline_start(self, domain: str) -> None:
        payload = json.dumps({"domain": domain})
        async with aiomqtt.Client(self._host, self._port) as client:
            await client.publish('recon/pipeline/start', payload)

    async def _handle_message(self, message, db):
        payload = json.loads(message.payload)
        if message.topic.matches('webapp/pipeline/step/start'):
            trace_id = payload['trace_id']
            topic = payload['topic']
            db.insert_pipeline_step_start(trace_id, topic)
        elif message.topic.matches('webapp/pipeline/step/end'):
            trace_id = payload['trace_id']
            topic = payload['topic']
            error = payload['error']
            db.insert_pipeline_step_end(
                trace_id, topic, error)
        elif message.topic.matches('webapp/pipeline/start'):
            trace_id = payload['trace_id']
            domain = payload['domain']
            db.insert_pipeline_start(trace_id, domain)
        else:
            print('unknown topic:', message.topic.value)
