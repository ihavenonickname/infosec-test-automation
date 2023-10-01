import json
from typing import NamedTuple

from helper import run_program
from log import LOGGER


class ProbeResultItem(NamedTuple):
    input_domain: str
    url: str
    status_code: int
    cnames: list
    techs: list


async def probe(domains: list) -> list:
    LOGGER.info('Probing %d domains', len(domains))

    args = ['httpx-toolkit', '-sc', '-td', '-json', '-probe']

    httpx_result = await run_program(*args, stdin_lines=domains)
    
    probe_result = []

    for line in httpx_result:
        LOGGER.debug('httpx result: %s', line)

        serialized_line: dict = json.loads(line)
        subdomain = serialized_line['input']

        if serialized_line['failed']:
            LOGGER.info('Subdomain %s is unresponsive', subdomain)
            continue

        item = ProbeResultItem(
            input_domain=subdomain,
            cnames=serialized_line.get('cnames'),
            url=serialized_line.get('url'),
            status_code=serialized_line.get('status-code'),
            techs=serialized_line.get('technologies'))

        LOGGER.info('Subdomain %s is responsive', item.input_domain)
        LOGGER.info('Subdomain %s replied %s', item.input_domain, item.status_code)
        LOGGER.info('Subdomain %s has full url %s', item.input_domain, item.url)
        LOGGER.info('Subdomain %s has canmes %s', item.input_domain, item.cnames)
        LOGGER.info('Subdomain %s has uses tech %s', item.input_domain, item.techs)

        probe_result.append(item)

    return probe_result
