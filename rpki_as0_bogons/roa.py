def as0_roas_for(bogons, maxLength):
    as0_roas = []

    for network in bogons:
        as0_roas.append(
            {"asn": 0, "prefix": str(network), "maxPrefixLength": maxLength}
        )

    return as0_roas
