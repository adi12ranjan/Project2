"""
parser.py — Email ingestion module.

Takes raw .eml bytes/text and extracts every structured field the rest of the
pipeline needs. Uses only Python's stdlib `email` package — no external
dependency, works fully offline.
"""
import re
from email import message_from_string, policy
from email.utils import parseaddr, getaddresses, parsedate_to_datetime


URL_RE = re.compile(r'https?://[^\s"\'<>\)\]]+', re.IGNORECASE)
IPV4_RE = re.compile(r'\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b')
DOMAIN_IN_TEXT_RE = re.compile(r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b')


def _addr_domain(address: str) -> str:
    if not address or '@' not in address:
        return ''
    return address.rsplit('@', 1)[-1].strip().lower()


def parse_eml(raw_text: str) -> dict:
    """Parse raw .eml text into a structured dict. Never raises on malformed
    input — degrades gracefully so the pipeline can still show *something*
    for a broken/partial upload."""
    msg = message_from_string(raw_text, policy=policy.default)

    from_header = msg.get('From', '') or ''
    to_header = msg.get('To', '') or ''
    reply_to_header = msg.get('Reply-To', '') or ''
    return_path_header = msg.get('Return-Path', '') or ''

    from_name, from_addr = parseaddr(from_header)
    _, reply_to_addr = parseaddr(reply_to_header)
    _, return_path_addr = parseaddr(return_path_header)
    to_list = [addr for _, addr in getaddresses([to_header]) if addr]

    date_raw = msg.get('Date', '')
    date_parsed = None
    if date_raw:
        try:
            date_parsed = parsedate_to_datetime(date_raw).isoformat()
        except Exception:
            date_parsed = None

    received_headers = msg.get_all('Received', []) or []

    # ---- body extraction (prefer text/plain, fall back to stripped html) ----
    body_text = ''
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get('Content-Disposition') or '')
            if 'attachment' in disp:
                continue
            if ctype == 'text/plain':
                try:
                    body_text += part.get_content()
                except Exception:
                    pass
        if not body_text:
            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    try:
                        html = part.get_content()
                        body_text += re.sub('<[^<]+?>', ' ', html)
                    except Exception:
                        pass
    else:
        try:
            body_text = msg.get_content()
            if msg.get_content_type() == 'text/html':
                body_text = re.sub('<[^<]+?>', ' ', body_text)
        except Exception:
            body_text = str(msg.get_payload())

    # ---- attachments ----
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            disp = str(part.get('Content-Disposition') or '')
            filename = part.get_filename()
            if filename or 'attachment' in disp:
                try:
                    payload = part.get_payload(decode=True) or b''
                except Exception:
                    payload = b''
                attachments.append({
                    'filename': filename or '(unnamed)',
                    'content_type': part.get_content_type(),
                    'size_bytes': len(payload),
                    'payload': payload,
                })

    # ---- URLs / domains found in the body ----
    urls_found = sorted(set(URL_RE.findall(body_text)))
    domains_from_urls = set()
    for u in urls_found:
        m = re.match(r'https?://([^/:\s]+)', u, re.IGNORECASE)
        if m:
            domains_from_urls.add(m.group(1).lower())

    # ---- authentication-results ----
    auth_results_headers = msg.get_all('Authentication-Results', []) or []

    return {
        'from_name': from_name,
        'from_addr': from_addr,
        'from_domain': _addr_domain(from_addr),
        'to_list': to_list,
        'reply_to_addr': reply_to_addr,
        'reply_to_domain': _addr_domain(reply_to_addr),
        'return_path_addr': return_path_addr,
        'return_path_domain': _addr_domain(return_path_addr),
        'subject': msg.get('Subject', '') or '',
        'date_raw': date_raw,
        'date_parsed': date_parsed,
        'message_id': msg.get('Message-ID', '') or '',
        'received_headers': list(received_headers),
        'auth_results_headers': list(auth_results_headers),
        'body_text': body_text.strip(),
        'urls': urls_found,
        'url_domains': sorted(domains_from_urls),
        'attachments': attachments,
        'all_headers': {k: v for k, v in msg.items()},
    }
