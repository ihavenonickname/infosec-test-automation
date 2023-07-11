from enum import Enum, auto
from helper import run_shell_command

from log import LOGGER


class SourcesDupsStrategy(Enum):
    ALLOW_DUPS = auto()
    PREFER_AMASS = auto()
    PREFER_SUBFINDER = auto()


class SubdomainEnumerator():
    def __init__(self, *, sources_dups_strategy: SourcesDupsStrategy):
        self._amass_custom_sources = ''
        self._subfinder_custom_sources = ''

        if sources_dups_strategy == SourcesDupsStrategy.ALLOW_DUPS:
            return

        amass_sources = set()
        amass_output = run_shell_command('amass', 'enum', '-list')

        for line in amass_output.splitlines():
            if line.endswith('*'):
                amass_sources.add(line[:25].strip().lower())

        LOGGER.info('amass sources: %s', amass_sources)

        subfinder_sources = set()
        subfinder_output = run_shell_command('subfinder', '-ls')

        for line in subfinder_output.splitlines():
            if not line.endswith('*'):
                subfinder_sources.add(line.strip().lower())

        LOGGER.info('subfinder sources: %s', subfinder_sources)

        if sources_dups_strategy == SourcesDupsStrategy.PREFER_SUBFINDER:
            amass_sources = amass_sources - subfinder_sources
            LOGGER.info('amass after removing duplicates: %s', amass_sources)
            self._amass_custom_sources = ','.join(amass_sources)
        elif sources_dups_strategy == SourcesDupsStrategy.PREFER_AMASS:
            subfinder_sources = subfinder_sources - amass_sources
            LOGGER.info('subfinder after removing duplicates: %s',
                        subfinder_sources)
            self._subfinder_custom_sources = ','.join(subfinder_sources)
        else:
            error_msg = 'Unknown option: %s', sources_dups_strategy
            LOGGER.info(error_msg)
            raise Exception(error_msg)

    def enumerate_subdomains(self, domain: str):
        amass_args = ['amass', 'enum', '-norecursive', '-passive', '-d', domain]
        subfinder_args = ['subfinder', '-silent', '-d', domain]

        if self._amass_custom_sources:
            amass_args.append('-include')
            amass_args.append(self._amass_custom_sources)
        elif self._subfinder_custom_sources:
            subfinder_args.append('-sources')
            subfinder_args.append(self._subfinder_custom_sources)

        output_amass = run_shell_command(*amass_args)
        subdomains_amass = set(output_amass.splitlines())
        LOGGER.info('amass found %d subdomains', len(subdomains_amass))

        output_subfinder = run_shell_command(*subfinder_args)
        subdomains_subfinder = set(output_subfinder.splitlines())
        LOGGER.info('subfinder found %d subdomains', len(subdomains_subfinder))

        return subdomains_amass.union(subdomains_subfinder)

    def recursively_enumerate_subdomains(self, domain: str):
        pending = [domain]
        seen = set()
        subdomains = set()

        while pending:
            current = pending.pop()

            if current in seen:
                continue

            seen.add(current)

            for subdomain in self.enumerate_subdomains(current):
                subdomains.add(subdomain)

                if subdomain not in seen:
                    pending.append(subdomain)

        return subdomains
