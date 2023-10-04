import aiomqtt

from helper import check_installed, loop_forever, run_program, ReconTopics
from log import LOGGER, extra


async def msg_handler(payload: dict, client: aiomqtt.Client):
    trace_id = payload['trace_id']
    domain = payload['domain']

    LOGGER.info('Starting DNS scan', extra=extra(trace_id, domain=domain))

    zonemaster_result = await run_program(
        'zonemaster-cli',
        '--no-progress',
        '--no-count',
        '--no-time',
        '--level',
        'WARNING',
        domain,
        trace_id=trace_id)

    if len(zonemaster_result) > 2:
        for line in zonemaster_result[2:]:
            i = line.index(' ')
            level, message = line[:i], line[i:].strip()
            LOGGER.info(
                'Found DNS vulnerability',
                extra=extra(trace_id, level=level, message=message))

    LOGGER.info('Finished DNS scan', extra=extra(trace_id))


async def run_main_loop():
    LOGGER.debug('Checking if tools are installed')

    if not await check_installed('zonemaster-cli'):
        LOGGER.critical('Some tools are not installed')
        return

    await loop_forever(
        topic_name=ReconTopics.DNS_VULN_SCAN,
        step_name='dns-vulnerability-scan',
        msg_handler=msg_handler)
