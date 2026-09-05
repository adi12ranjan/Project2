"""
ioc_extractor.py — Indicator of Compromise extraction.

Pulls every IP, domain, URL, email address and attachment hash out of the
parsed email and the relay chain, then assigns each one a risk level using
simple, explainable heuristics (no external threat-intel API required, so
this always works offline).
"""
import hashlib
import re

SUSPICIOUS_TLDS = {'.ru', '.tk', '.top', '.xyz', '.click', '.zip', '.gq', '.cf', '.ml', '.support', '.fit'}
URL_SHORTENERS = {'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'is.gd', 'buff.ly'}
DANGEROUS_EXTENSIONS = {'.exe', '.scr', '.js', '.vbs', '.jar', '.bat', '.cmd', '.msi', '.docm', '.xlsm', '.pptm', '.iso', '.lnk'}


def _domain_risk(domain: str) -> str:
    if not domain:
        return 'unknown'
    d = domain.lower()
    if any(d.endswith(tld) for tld in SUSPICIOUS_TLDS):
        return 'high'
    if d in URL_SHORTENERS:
        return 'high'
    if re.search(r'\d{2,}', d.split('.')[0]):
        return 'medium'
    return 'low'


def _ip_risk(ip: str, relay_hops: list, geo_lookup: dict = None) -> str:
    for hop in relay_hops:
        if hop.get('ip') == ip and hop.get('suspicious'):
            return 'high'
    if geo_lookup:
        entry = geo_lookup.get(ip)
        if entry:
            isp = (entry.get('isp') or '').lower()
            if any(kw in isp for kw in ('hosting', 'tor exit', 'vps', 'bulletproof', 'offshore')):
                return 'high'
    for hop in relay_hops:
        if hop.get('ip') == ip and hop.get('is_origin'):
            return 'medium'
    return 'low'


def _url_risk(url: str) -> str:
    m = re.match(r'https?://([^/:\s]+)', url, re.IGNORECASE)
    host = m.group(1).lower() if m else ''
    if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', host):
        return 'high'  # raw IP in URL — classic phishing/credential-harvest pattern
    if host in URL_SHORTENERS:
        return 'high'
    if any(host.endswith(tld) for tld in SUSPICIOUS_TLDS):
        return 'high'
    if '@' in url or url.count('-') >= 3:
        return 'medium'
    return 'low'


def extract_iocs(parsed: dict, relay_hops: list, geo_lookup: dict = None) -> list:
    iocs = []
    seen = set()

    def add(ioc_type, value, risk, note=''):
        key = (ioc_type, value)
        if key in seen or not value:
            return
        seen.add(key)
        iocs.append({'type': ioc_type, 'value': value, 'risk': risk, 'note': note})

    # IPs from the relay chain
    for hop in relay_hops:
        if hop.get('ip'):
            note = 'Origin hop' if hop.get('is_origin') else ''
            add('ip', hop['ip'], _ip_risk(hop['ip'], relay_hops, geo_lookup), note)

    # Domains: from-address, reply-to, return-path
    add('domain', parsed.get('from_domain', ''), _domain_risk(parsed.get('from_domain', '')), 'Sender domain')
    if parsed.get('reply_to_domain'):
        add('domain', parsed['reply_to_domain'], _domain_risk(parsed['reply_to_domain']), 'Reply-To domain')
    if parsed.get('return_path_domain'):
        add('domain', parsed['return_path_domain'], _domain_risk(parsed['return_path_domain']), 'Return-Path domain')

    # URLs found in body + their domains
    for url in parsed.get('urls', []):
        add('url', url, _url_risk(url))
    for d in parsed.get('url_domains', []):
        add('domain', d, _domain_risk(d), 'Linked in email body')

    # Email addresses
    add('email', parsed.get('from_addr', ''), 'low', 'Sender address')
    if parsed.get('reply_to_addr') and parsed['reply_to_addr'] != parsed.get('from_addr'):
        add('email', parsed['reply_to_addr'], 'medium', 'Reply-To address')

    # Attachment hashes
    for att in parsed.get('attachments', []):
        payload = att.get('payload', b'') or b''
        sha256 = hashlib.sha256(payload).hexdigest() if payload else None
        ext = ''
        if '.' in att.get('filename', ''):
            ext = '.' + att['filename'].rsplit('.', 1)[-1].lower()
        risk = 'high' if ext in DANGEROUS_EXTENSIONS else ('medium' if ext in ('.zip', '.rar', '.7z') else 'low')
        if sha256:
            add('hash', sha256, risk, f"SHA-256 of attachment '{att.get('filename')}'")

    return iocs
