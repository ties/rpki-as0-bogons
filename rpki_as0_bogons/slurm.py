#!/usr/bin/env python3
# Copyright (c) 2020, Massimiliano Stucchi
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import argparse
import csv
import json
import logging
import ipaddress

import requests


logging.basicConfig()
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


UNASSIGNED_STATUSES = set(["available", "ianapool", "ietf", "reserved"])


def main():

    parser = argparse.ArgumentParser(
        description="A script to generate a SLURM file for all bogons with origin AS0"
    )

    parser.add_argument(
        "-f",
        dest="dest_file",
        default="/usr/local/etc/bogons.slurm.txt",
        help="File to be created with all the SLURM content",
    )

    parser.add_argument(
        "--use-delegated-stats",
        dest="use_delegated_stats",
        default=False,
        action="store_true",
        help="Enable the use of NRO delegated stats (EXPERIMENTAL - default bogons list will not be taken in consideration)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        default=False,
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        LOG.setLevel(logging.DEBUG)

    roas = []
    if args.use_delegated_stats:
        delegated_stats_url = (
            "https://www.nro.net/wp-content/uploads/apnic-uploads/delegated-extended"
        )
        roas = nro_as0_roas(delegated_stats_url)
    else:
        ipv4_cymru_bogons_url = (
            "https://www.team-cymru.org/Services/Bogons/fullbogons-ipv4.txt"
        )
        ipv6_cymru_bogons_url = (
            "https://www.team-cymru.org/Services/Bogons/fullbogons-ipv6.txt"
        )

        roas = cymru_as0_roas(ipv4_cymru_bogons_url, 32) + cymru_as0_roas(
            ipv6_cymru_bogons_url, 128
        )

    output = {}

    output["slurmVersion"] = 1
    output["validationOutputFilters"] = {}
    output["validationOutputFilters"]["prefixFilters"] = []
    output["validationOutputFilters"]["bgpsecFilter"] = []
    output["locallyAddedAssertions"] = {}
    output["locallyAddedAssertions"]["prefixAssertions"] = []
    output["locallyAddedAssertions"]["bgpsecAssertions"] = []

    output["locallyAddedAssertions"]["prefixAssertions"] = roas

    with open(args.dest_file, "w") as f:
        f.write(json.dumps(output, indent=2))


def cymru_as0_roas(url, maxLength):
    bogons = requests.get(url).text.split("\n")
    # Remove the first and the last line
    bogons.pop(0)  # # last updated 1581670201 (Fri Feb 14 08:50:01 2020 GMT)
    bogons.pop()  # <last empty line on the file>

    return as0_roas_for(bogons, maxLength)


def nro_as0_roas(url):
    LOG.debug("Retrieving %s", url)
    res = requests.get(url)
    assert res.status_code == 200

    delegations = list(csv.reader(res.text.split("\n"), delimiter="|"))
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


def as0_roas_for(bogons, maxLength):
    as0_roas = []

    for network in bogons:
        as0_roas.append(
            {"asn": 0, "prefix": str(network), "maxPrefixLength": maxLength}
        )

    return as0_roas


if __name__ == "__main__":
    main()
