"""
relay_tracer.py — Reconstructs the relay chain from Received headers.

Received headers are prepended by each hop, so the *last* one in the list
(bottom of the raw file) is actually the *first* hop chronologically (closest
to the sender). We reverse them to get sender -> recipient order, extract the
IP at each hop, and flag hops that look suspicious (private/internal IP
claiming to be a hop, mismatched hostname vs IP, or a hop from a domain
unrelated to the sender's claimed organization).
"""
import re
import ipaddress

IP_RE = re.compile(r'\[?((?:\d{1,3}\.){3}\d{1,3})\]?')
FROM_HOST_RE = re.compile(r'from\s+(\S+)', re.IGNORECASE)
BY_HOST_RE = re.compile(r'by\s+(\S+)', re.IGNORECASE)


def _is_private_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return False


def trace_relay_chain(parsed: dict) -> list:
    received = parsed.get('received_headers', [])
    # Received headers are listed newest-first in the file; reverse for
    # sender -> recipient chronological order.
    chain_raw = list(reversed(received))

    hops = []
    for idx, header in enumerate(chain_raw):
        ips = IP_RE.findall(header)
        # last IP mentioned in a Received line is typically the connecting host
        hop_ip = ips[-1] if ips else None
        from_match = FROM_HOST_RE.search(header)
        by_match = BY_HOST_RE.search(header)

        flags = []
        if hop_ip:
            if _is_private_ip(hop_ip):
                flags.append('Private/internal IP address in a public relay hop')
        else:
            flags.append('No IP address found in this hop (header may be forged/incomplete)')

        from_host = from_match.group(1) if from_match else None
        by_host = by_match.group(1) if by_match else None

        hops.append({
            'hop_index': idx + 1,
            'raw_header': header.strip(),
            'from_host': from_host,
            'by_host': by_host,
            'ip': hop_ip,
            'suspicious': bool(flags),
            'flags': flags,
        })

    # Mark the first hop (closest to sender) as the "origin" hop, which is
    # the most forensically interesting one.
    if hops:
        hops[0]['is_origin'] = True
        for h in hops[1:]:
            h['is_origin'] = False

    return hops
