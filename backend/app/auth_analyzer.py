"""
auth_analyzer.py — Email authentication analysis.

Parses the Authentication-Results header (RFC 8601) to extract SPF, DKIM and
DMARC verdicts, and separately checks header alignment (From vs Reply-To vs
Return-Path domains) — a classic BEC/spoofing indicator regardless of what
SPF/DKIM/DMARC say, since those can pass on a *different* freshly-registered
lookalike domain.
"""
import re


def _extract_verdict(auth_header_text: str, mechanism: str) -> str:
    """Returns 'pass' / 'fail' / 'softfail' / 'neutral' / 'none' / 'unknown'."""
    m = re.search(rf'{mechanism}\s*=\s*(\w+)', auth_header_text, re.IGNORECASE)
    if not m:
        return 'unknown'
    return m.group(1).lower()


def analyze_authentication(parsed: dict) -> dict:
    combined = ' '.join(parsed.get('auth_results_headers', []))

    spf = _extract_verdict(combined, 'spf') if combined else 'unknown'
    dkim = _extract_verdict(combined, 'dkim') if combined else 'unknown'
    dmarc = _extract_verdict(combined, 'dmarc') if combined else 'unknown'

    from_domain = parsed.get('from_domain', '')
    reply_to_domain = parsed.get('reply_to_domain', '')
    return_path_domain = parsed.get('return_path_domain', '')

    reply_to_mismatch = bool(reply_to_domain and reply_to_domain != from_domain)
    return_path_mismatch = bool(return_path_domain and return_path_domain != from_domain)

    issues = []
    if spf in ('fail', 'softfail'):
        issues.append(f'SPF {spf} — sending server is not authorized for this domain')
    if dkim in ('fail', 'none'):
        issues.append('DKIM signature missing or invalid — message integrity cannot be verified')
    if dmarc == 'fail':
        issues.append('DMARC alignment failed — domain owner policy was violated')
    if reply_to_mismatch:
        issues.append(f'Reply-To domain ({reply_to_domain}) differs from From domain ({from_domain})')
    if return_path_mismatch:
        issues.append(f'Return-Path domain ({return_path_domain}) differs from From domain ({from_domain})')

    return {
        'spf': spf,
        'dkim': dkim,
        'dmarc': dmarc,
        'from_domain': from_domain,
        'reply_to_domain': reply_to_domain or None,
        'return_path_domain': return_path_domain or None,
        'reply_to_mismatch': reply_to_mismatch,
        'return_path_mismatch': return_path_mismatch,
        'issues': issues,
    }
