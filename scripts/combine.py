#!/usr/bin/env python3
"""Combine cidr/*_v4.txt and cidr/*_v6.txt into UniFi-friendly lists.

UniFi Network Lists silently drop host routes written as /32 (or /128) and
CIDRs with host bits set, so entries are normalised, aggregated, and single
hosts are written as bare addresses.
"""
import glob
import ipaddress
import sys

MIN_ENTRIES = 10


def load(pattern, version):
    nets, bad = [], 0
    files = sorted(glob.glob(pattern))
    if not files:
        sys.exit(f"no source files for {pattern}")
    for path in files:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue
                try:
                    net = ipaddress.ip_network(line, strict=False)
                except ValueError:
                    bad += 1
                    continue
                if net.version == version:
                    nets.append(net)
    return files, nets, bad


def write(out, nets, version):
    full = 32 if version == 4 else 128
    collapsed = list(ipaddress.collapse_addresses(nets))
    with open(out, "w") as fh:
        for n in collapsed:
            fh.write(f"{n.network_address}\n" if n.prefixlen == full else f"{n}\n")
    return len(collapsed)


for version, pattern, out in (
    (4, "cidr/*_v4.txt", "combined/scanners_v4.txt"),
    (6, "cidr/*_v6.txt", "combined/scanners_v6.txt"),
):
    files, nets, bad = load(pattern, version)
    count = write(out, nets, version)
    if count < MIN_ENTRIES:
        sys.exit(f"{out}: only {count} entries, aborting")
    print(f"{out}: {count} entries from {len(files)} files ({len(nets)} raw, {bad} unparsable)")
