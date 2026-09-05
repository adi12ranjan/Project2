"""
pipeline.py — Orchestrates the full analysis pipeline end to end.
This is the single function the API layer calls; every module it touches is
independently unit-tested (see the module docstrings).
"""
import uuid
from datetime import datetime, timezone

from .parser import parse_eml
from .auth_analyzer import analyze_authentication
from .relay_tracer import trace_relay_chain
from .ioc_extractor import extract_iocs
from .threat_detector import detect_threats
from .risk_scorer import score_email
from .geolocation import geolocate_all
from .graph_builder import build_graph
from .report_generator import generate_report
from . import database


def run_pipeline(raw_eml_text: str, filename: str = 'uploaded.eml') -> dict:
    parsed = parse_eml(raw_eml_text)
    auth = analyze_authentication(parsed)
    relay_hops = trace_relay_chain(parsed)
    threats = detect_threats(parsed, auth, relay_hops)

    relay_ips = [h['ip'] for h in relay_hops if h.get('ip')]
    geo = geolocate_all(relay_ips)
    geo_lookup = {g['ip']: g for g in geo}

    iocs = extract_iocs(parsed, relay_hops, geo_lookup)
    risk = score_email(auth, threats, relay_hops)

    graph = build_graph(parsed, auth, iocs, relay_hops, geo)

    investigation_id = str(uuid.uuid4())[:8]
    created_at = datetime.now(timezone.utc).isoformat()

    # strip raw attachment bytes before persisting/returning (keep metadata only)
    parsed_public = dict(parsed)
    parsed_public['attachments'] = [
        {k: v for k, v in att.items() if k != 'payload'} for att in parsed.get('attachments', [])
    ]

    analysis = {
        'investigation_id': investigation_id,
        'filename': filename,
        'created_at': created_at,
        'parsed': parsed_public,
        'authentication': auth,
        'relay_chain': relay_hops,
        'threats': threats,
        'iocs': iocs,
        'geolocation': geo,
        'graph': graph,
        'risk': risk,
    }

    report_md = generate_report(investigation_id, parsed_public, auth, threats, iocs, relay_hops, geo, risk)
    analysis['report_markdown'] = report_md

    database.save_investigation(investigation_id, filename, parsed_public, risk, iocs, analysis, created_at)

    return analysis
