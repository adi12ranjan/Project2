"""
report_generator.py — Produces a professional Markdown forensic report from
a completed analysis. Markdown is chosen over PDF for the MVP because it
needs zero extra dependencies, renders cleanly in GitHub/most viewers, and
can still be downloaded/printed by the analyst.
"""
from datetime import datetime, timezone


RECOMMENDED_ACTIONS = {
    'CRITICAL': [
        'Quarantine this email immediately',
        'Block the sending domain and all identified malicious IPs',
        'Alert the targeted employee(s) directly — do not rely on email',
        'Escalate to the security team / SOC for full incident response',
        'If financial details were shared, contact the bank to halt any pending transaction',
    ],
    'HIGH RISK': [
        'Quarantine this email pending review',
        'Block the sending domain',
        'Investigate the origin IP address',
        'Notify the recipient not to click links or reply',
    ],
    'SUSPICIOUS': [
        'Flag for manual review by the security team',
        'Advise the recipient to verify the sender through a separate channel before acting',
        'Monitor the sending domain for further activity',
    ],
    'SAFE': [
        'No action required',
        'Continue standard monitoring',
    ],
}


def generate_report(investigation_id: str, parsed: dict, auth: dict, threats: dict,
                     iocs: list, relay_hops: list, geo: list, risk: dict) -> str:
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = []
    a = lines.append

    a(f"# Email Forensic Investigation Report")
    a(f"**Investigation ID:** `{investigation_id}`  ")
    a(f"**Generated:** {now}  ")
    a(f"**Classification:** {risk['classification']}  ")
    a(f"**Threat Score:** {risk['score']}/100  ")
    a(f"**Confidence:** {risk['confidence']}%\n")

    a("## Incident Summary")
    a(f"- **From:** {parsed.get('from_name') or ''} <{parsed.get('from_addr')}>")
    a(f"- **To:** {', '.join(parsed.get('to_list', []))}")
    a(f"- **Subject:** {parsed.get('subject')}")
    a(f"- **Date:** {parsed.get('date_raw')}")
    a(f"- **Message-ID:** `{parsed.get('message_id')}`\n")

    a("## Authentication Results")
    a(f"| Check | Result |")
    a(f"|---|---|")
    a(f"| SPF | {auth.get('spf')} |")
    a(f"| DKIM | {auth.get('dkim')} |")
    a(f"| DMARC | {auth.get('dmarc')} |")
    a(f"| Reply-To mismatch | {'Yes — ' + str(auth.get('reply_to_domain')) if auth.get('reply_to_mismatch') else 'No'} |")
    a(f"| Return-Path mismatch | {'Yes — ' + str(auth.get('return_path_domain')) if auth.get('return_path_mismatch') else 'No'} |\n")

    a("## Detection Reasons (why this score was produced)")
    if risk['reasons']:
        for r in risk['reasons']:
            a(f"- **+{r['weight']}** [{r['category']}] {r['text']}")
    else:
        a("- No threat signals were detected.")
    a("")

    a("## Relay Path (Received header chain, sender → recipient)")
    for hop in relay_hops:
        marker = ' ⚠️ SUSPICIOUS' if hop.get('suspicious') else ''
        origin = ' (origin)' if hop.get('is_origin') else ''
        a(f"{hop['hop_index']}. `{hop.get('ip') or 'no IP'}` — {hop.get('from_host') or 'unknown host'}{origin}{marker}")
    a("")

    a("## Geographic Intelligence")
    a("*Note: geolocation data below is from a bundled demo dataset for offline demonstration purposes.*\n")
    for g in geo:
        a(f"- `{g['ip']}` → {g['city']}, {g['country']} ({g.get('isp', 'unknown ISP')}, {g.get('asn', '')})")
    a("")

    a("## Indicators of Compromise (IOCs)")
    a("| Type | Value | Risk |")
    a("|---|---|---|")
    for ioc in iocs:
        a(f"| {ioc['type']} | `{ioc['value']}` | {ioc['risk']} |")
    a("")

    a("## Recommended Actions")
    for action in RECOMMENDED_ACTIONS.get(risk['classification'], []):
        a(f"- {action}")
    a("")

    a("---")
    a("*This report was generated automatically by an explainable rule-based detection engine. "
      "No score in this report is a machine-learning confidence percentage — every point is tied "
      "to a specific, listed reason above.*")

    return '\n'.join(lines)
