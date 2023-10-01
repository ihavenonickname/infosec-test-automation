import argparse
import asyncio

import log
from prober import probe
from subdomain_enumeration import enumerate_subdomains


async def main():
    log.configure()

    parser = argparse.ArgumentParser(
        prog='Recon Pipeline',
        description='My personal pipeline for recon operations')

    parser.add_argument(
        '--domain',
        help='Enumerate the subdomains under the given domain',
        required=True)

    args = parser.parse_args()

    # TODO: Check if tools are installed

    subdomains = await enumerate_subdomains(args.domain)

    probe_results = await probe(subdomains)

if __name__ == '__main__':
    asyncio.run(main())
