import ipaddress
import logging

from .roa import as0_roas_for

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


UNASSIGNED_STATUSES = set(["available", "ianapool", "ietf", "reserved"])


def generate_slurm(data):
    delegations = list(csv.reader(data.split("\n"), delimiter="|"))
    LOG.debug("Loaded %d delegations", len(delegations))
    # Ignore final blank line
    delegations.pop()
    # Ignore the first four lines with header and  summaries
    delegations = delegations[4:]
    # 2|nro|20200214|574416|19821213|20200214|+0000
    # nro|*|asn|*|91534|summary
    # nro|*|ipv4|*|214428|summary
    # nro|*|ipv6|*|268454|summary

    roas = []
    import ipdb

    ipdb.set_trace()

    for delegation in delegations:
        rir, country, object_type, value, length, date, status, _, _ = delegation
        length = int(length)

        if status in UNASSIGNED_STATUSES:
            if object_type == "ipv4":
                v4networks = ipaddress.summarize_address_range(
                    ipaddress.IPv4Address(value),
                    ipaddress.IPv4Address(value) + (length - 1),
                )
                roas += as0_roas_for(v4networks, 32)
            if object_type == "ipv6":
                v6networks = [ipaddress.IPv6Network((value, length))]
                roas += as0_roas_for(v6networks, 128)

    return roas
