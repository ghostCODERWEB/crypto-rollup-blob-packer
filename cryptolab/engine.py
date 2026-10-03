"""Pack indivisible payloads into bounded data containers using deterministic first-fit decreasing and report unused capacity."""

from .common import (
    number,
    integer,
    identity,
    records,
    chronology,
    allocate,
    result,
    validate_document,
)
from decimal import Decimal


def _analyze(d):
    capacity = integer(d["capacity"], 1)
    overhead = integer(d["overhead"], maximum=capacity)
    limit = integer(d["maximum_containers"], 1)
    payloads = []
    for p in records(d["payloads"], "id"):
        size = integer(p["bytes"], 1)
        if size + overhead > capacity:
            raise ValueError("payload exceeds usable capacity")
        payloads.append({"id": p["id"], "bytes": size})
    bins = []
    rejected = []
    for p in sorted(payloads, key=lambda p: (-p["bytes"], p["id"])):
        target = next((b for b in bins if b["used"] + p["bytes"] <= capacity), None)
        if target is None:
            if len(bins) == limit:
                rejected.append(p["id"])
                continue
            target = {"payloads": [], "used": overhead}
            bins.append(target)
        target["payloads"].append(p["id"])
        target["used"] += p["bytes"]
    for b in bins:
        b["unused"] = capacity - b["used"]
    return {
        "containers": bins,
        "rejected": rejected,
        "payload_bytes": sum(b["used"] - overhead for b in bins),
        "unused_bytes": sum(b["unused"] for b in bins),
        "container_count": len(bins),
    }


def analyze(document):
    validate_document(document)
    try:
        return result(_analyze(document))
    except (KeyError, TypeError, ArithmeticError, RecursionError) as error:
        raise ValueError("invalid domain input: " + str(error)) from error
