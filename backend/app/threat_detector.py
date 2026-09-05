"""
threat_detector.py — Rule-based phishing / BEC / impersonation detection.

Deliberately generalizable: lookalike-domain detection works by comparing the
sender's domain against (a) the recipient's own organization domain (catches
"impersonate our own CEO on a typo domain") and (b) a small list of globally
recognized brand names (catches "impersonate PayPal/Microsoft/etc."), using
edit-distance + homoglyph substitution — not a per-email hardcoded rule.
"""
import re

URGENCY_KEYWORDS = [
    'urgent', 'immediately', 'right away', 'action required', 'act now',
    'within 24 hours', 'within the hour', 'time-sensitive', 'time sensitive',
    'asap', 'expire', 'suspend', 'suspended', 'locked', 'final notice',
    'do not ignore', "don't ignore", 'before end of day', 'confidential',
]
FINANCIAL_KEYWORDS = [
    'wire transfer', 'wire $', 'bank account', 'routing number', 'account number',
    'payment', 'invoice', 'gift card', 'gift cards', 'beneficiary', 'swift code',
    'iban', 'crypto', 'bitcoin', 'western union',
]
CREDENTIAL_KEYWORDS = [
    'verify your account', 'verify your identity', 'confirm your account',
    'click here to confirm', 'update your password', 'reset your password',
    'enter your password', 'login to verify', 'restore access', 'card details',
    'social security number', 'date of birth', 'employee names',
]
SECRECY_KEYWORDS = [
    "don't discuss", 'do not discuss', 'do not tell', "don't tell", 'keep this confidential',
    'between us', "can't take calls", 'cannot take calls', 'in a meeting',
]
KNOWN_BRANDS = {
    'paypal': 'paypal.com', 'microsoft': 'microsoft.com', 'google': 'google.com',
    'amazon': 'amazon.com', 'apple': 'apple.com', 'chase': 'chase.com',
    'bankofamerica': 'bankofamerica.com', 'wellsfargo': 'wellsfargo.com',
    'docusign': 'docusign.com', 'office365': 'office.com',
}
LEET_MAP = str.maketrans({'1': 'l', '0': 'o', '3': 'e', '4': 'a', '5': 's', '@': 'a'})


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[lb]


def _keyword_hits(text: str, keywords: list) -> list:
    t = text.lower()
    return [kw for kw in keywords if kw in t]


def _check_lookalike_domain(from_domain: str, recipient_domains: list) -> dict:
    """Compares sender domain against recipient org domains and known brands."""
    if not from_domain:
        return {'is_lookalike': False}

    candidates = []
    for rd in recipient_domains:
        if rd and rd != from_domain:
            candidates.append(rd)
    for brand, brand_domain in KNOWN_BRANDS.items():
        candidates.append(brand_domain)

    normalized_from = from_domain.translate(LEET_MAP)

    best = None
    for candidate in candidates:
        if from_domain == candidate:
            continue
        dist = _levenshtein(normalized_from.split('.')[0], candidate.split('.')[0])
        # also check "brand name appears inside a longer suspicious domain"
        brand_label = candidate.split('.')[0]
        contains_brand = brand_label in normalized_from and from_domain != candidate
        if dist <= 2 and dist > 0 or contains_brand:
            if best is None or dist < best['edit_distance']:
                best = {'target': candidate, 'edit_distance': dist, 'contains_brand': contains_brand}

    if best:
        return {'is_lookalike': True, **best}
    return {'is_lookalike': False}


def detect_threats(parsed: dict, auth: dict, relay_hops: list) -> dict:
    body = parsed.get('body_text', '') or ''
    subject = parsed.get('subject', '') or ''
    combined_text = f'{subject}\n{body}'

    urgency_hits = _keyword_hits(combined_text, URGENCY_KEYWORDS)
    financial_hits = _keyword_hits(combined_text, FINANCIAL_KEYWORDS)
    credential_hits = _keyword_hits(combined_text, CREDENTIAL_KEYWORDS)
    secrecy_hits = _keyword_hits(combined_text, SECRECY_KEYWORDS)

    recipient_domains = [addr.split('@')[-1].lower() for addr in parsed.get('to_list', []) if '@' in addr]
    lookalike = _check_lookalike_domain(parsed.get('from_domain', ''), recipient_domains)

    # executive impersonation: display name suggests authority/exec, but
    # domain is external/unaligned or a lookalike
    exec_terms = ['ceo', 'cfo', 'president', 'director', 'chief executive', 'chief financial']
    from_name_lower = (parsed.get('from_name') or '').lower()
    claims_exec = any(term in from_name_lower for term in exec_terms) or any(term in body.lower()[:400] for term in exec_terms)
    exec_impersonation = claims_exec and (lookalike['is_lookalike'] or auth.get('dmarc') == 'fail')

    # suspicious / dangerous URLs
    suspicious_urls = []
    for url in parsed.get('urls', []):
        m = re.match(r'https?://([^/:\s]+)', url, re.IGNORECASE)
        host = m.group(1).lower() if m else ''
        if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', host):
            suspicious_urls.append({'url': url, 'reason': 'Raw IP address used instead of a domain name'})
        elif host.translate(LEET_MAP) != host or any(b in host.translate(LEET_MAP) for b in KNOWN_BRANDS if b not in host):
            suspicious_urls.append({'url': url, 'reason': 'Domain uses character substitution resembling a known brand'})

    # dangerous attachments
    dangerous_attachments = []
    for att in parsed.get('attachments', []):
        fn = att.get('filename', '') or ''
        if '.' in fn:
            ext = '.' + fn.rsplit('.', 1)[-1].lower()
            if ext in ('.exe', '.scr', '.js', '.vbs', '.jar', '.bat', '.cmd', '.msi', '.docm', '.xlsm', '.pptm', '.iso', '.lnk'):
                dangerous_attachments.append({'filename': fn, 'reason': f'Executable/macro-capable file type ({ext})'})

    return {
        'urgency_keywords': urgency_hits,
        'financial_keywords': financial_hits,
        'credential_keywords': credential_hits,
        'secrecy_keywords': secrecy_hits,
        'lookalike_domain': lookalike,
        'executive_impersonation': exec_impersonation,
        'suspicious_urls': suspicious_urls,
        'dangerous_attachments': dangerous_attachments,
    }
