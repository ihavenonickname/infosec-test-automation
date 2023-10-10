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
from open_observe_api import OpenObserveApi


MQTT_HOST = os.environ['MQTT_HOST']
MQTT_PORT = os.environ['MQTT_PORT']
DATA_DIR = os.environ['DATA_DIR']
OPEN_OBSERVE_BASE_URL = os.environ['OPEN_OBSERVE_BASE_URL']
OPEN_OBSERVE_ROOT_EMAIL = os.environ['OPEN_OBSERVE_ROOT_EMAIL']
OPEN_OBSERVE_ROOT_PASSWORD = os.environ['OPEN_OBSERVE_ROOT_PASSWORD']

DATABASE = Database(os.path.join(DATA_DIR, 'webapp.db'))
MESSAGING_API = MessagingApi(MQTT_HOST, int(MQTT_PORT))
OPEN_OBSERVE_API = OpenObserveApi(
    OPEN_OBSERVE_BASE_URL, OPEN_OBSERVE_ROOT_EMAIL, OPEN_OBSERVE_ROOT_PASSWORD)


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


@app.get('/users', response_class=HTMLResponse)
def get_users(request: Request):
    ok, data = OPEN_OBSERVE_API.list_users()

    if not ok:
        raise HTTPException(status_code=500, detail='Could not list users')

    return templates.TemplateResponse('users.html', {
        'request': request,
        'users': data['data'],
    })


@app.get('/users/create', response_class=HTMLResponse)
def get_users_create(request: Request):
    return templates.TemplateResponse('users-create.html', {
        'request': request,
    })


@app.post('/users')
async def post_users(model: CreateUserModel):
    ok, data = OPEN_OBSERVE_API.create_user(
        model.email, model.first_name, model.last_name, model.password)

    if ok:
        return Response(status_code=204)

    raise HTTPException(
        status_code=400, detail=data if data else 'Unexpected error')


@app.delete('/users/{email}')
def delete_users(email: str):
    ok, data = OPEN_OBSERVE_API.delete_user(email)

    if ok:
        return Response(status_code=204)

    raise HTTPException(
        status_code=400, detail=data if data else 'Unexpected error')


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
        execution['logs_url'] = f'{OPEN_OBSERVE_BASE_URL}/web/logs?stream=default&period=15d&refresh=0&sql_mode=false&query={query}&org_identifier=recon'

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
