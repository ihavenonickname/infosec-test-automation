import asyncio
from helper import run_program

from log import LOGGER


async def enumerate_subdomains(domain):
    LOGGER.debug('Starting domain enumeration')

    async with asyncio.TaskGroup() as tg:
        amass_task = tg.create_task(
            run_program('amass', 'enum', '-passive', '-norecursive', '-silent', '-d', domain))
        subfinder_task = tg.create_task(
            run_program('subfinder', '-silent', '-d', domain))
        findomain_task = tg.create_task(
            run_program('findomain', '-q', '-t', domain))

    LOGGER.debug('Enumeration completed')

    subdomains = {
        *amass_task.result(),
        *subfinder_task.result(),
        *findomain_task.result(),
    }

    for subdomain in subdomains:
        LOGGER.info('Enumerated subdomain %s', subdomain)

    return subdomains
