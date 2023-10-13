import asyncio
import base64
import contextlib
import os

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import validators

from database import Database
from messaging import MessagingApi


MQTT_HOST = os.environ['MQTT_HOST']
MQTT_PORT = os.environ['MQTT_PORT']
DATA_DIR = os.environ['DATA_DIR']

DATABASE = Database(os.path.join(DATA_DIR, 'webapp.db'))
MESSAGING_API = MessagingApi(MQTT_HOST, int(MQTT_PORT))


@contextlib.asynccontextmanager
async def lifespan(app):
    coro = MESSAGING_API.loop_forever(DATABASE)
    task = asyncio.create_task(coro)

    print('yielding...')
    yield
    print('...yielded')

    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)

app.mount(
    '/static',
    StaticFiles(directory='./static'),
    'static')

templates = Jinja2Templates(directory='./src/templates')


class StartReconPipelineModel(BaseModel):
    domain: str


class CreateUserModel(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str


@app.get('/', response_class=HTMLResponse)
def get_index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.post('/pipelines')
async def post_start_recon_pipeline(model: StartReconPipelineModel):
    if not validators.domain(model.domain):
        raise HTTPException(status_code=400, detail='Domain is invalid')

    await MESSAGING_API.send_pipeline_start(model.domain)


@app.get('/pipelines')
def get_updates(count: int, last_trace_id: str | None = None):
    executions = DATABASE.fetch_pipeline_executions(count, last_trace_id)

    for execution in executions:
        trace_id = execution['trace_id']
        query = base64.b64encode(
            f"trace_id='{trace_id}'".encode('utf8')).decode('ascii')

    return executions


@app.get('/{path:path}')
def redirect_to_index():
    return RedirectResponse(url='/')


if __name__ == '__main__':
    try:
        uvicorn.run(app, host='0.0.0.0', port=8000)
    finally:
        print('Closing DB_CON')
        DATABASE.close()
        print('DB_CON closed')
