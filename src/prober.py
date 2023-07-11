import json
from typing import NamedTuple

from helper import run_shell_command
from log import LOGGER


class ProbeResultItem(NamedTuple):
    input_domain: str
    url: str
    status_code: int
    cnames: list
    techs: list


def probe(domains: list) -> list:
    LOGGER.info('Probing %d domains', len(domains))

    output = run_shell_command(
        'httpx-toolkit', '-sc', '-td', '-json', '-probe',
        input_lines=domains)

    result = []

    for line in output.splitlines():
        serialized_line: dict = json.loads(line)

        if serialized_line['failed']:
            continue

        item = ProbeResultItem(
            input_domain=serialized_line['input'],
            cnames=serialized_line.get('cnames'),
            url=serialized_line.get('url'),
            status_code=serialized_line.get('status-code'),
            techs=serialized_line.get('technologies'))

        result.append(item)

    return result
