"""
graph_builder.py — Builds a node/edge graph for the investigation visualization.

Output format is intentionally generic (id/label/type/risk on nodes;
source/target on edges) so it drops straight into React Flow or Cytoscape.js
on the frontend without any transformation.
"""


def build_graph(parsed: dict, auth: dict, iocs: list, relay_hops: list, geo: list) -> dict:
    nodes = []
    edges = []
    seen_nodes = set()

    def add_node(node_id, label, node_type, risk='low', extra=None):
        if node_id in seen_nodes:
            return
        seen_nodes.add(node_id)
        nodes.append({'id': node_id, 'label': label, 'type': node_type, 'risk': risk, **(extra or {})})

    def add_edge(source, target, label=''):
        edges.append({'source': source, 'target': target, 'label': label})

    email_id = 'email:root'
    add_node(email_id, parsed.get('subject') or '(no subject)', 'email', 'medium')

    sender_id = f"sender:{parsed.get('from_addr')}"
    add_node(sender_id, parsed.get('from_addr') or 'Unknown sender', 'sender',
              'high' if (auth.get('spf') == 'fail' or auth.get('dmarc') == 'fail') else 'low')
    add_edge(sender_id, email_id, 'sent')

    domain_id = f"domain:{parsed.get('from_domain')}"
    add_node(domain_id, parsed.get('from_domain') or 'unknown-domain', 'domain',
              'high' if auth.get('dmarc') == 'fail' else 'low')
    add_edge(domain_id, sender_id, 'owns')

    if auth.get('reply_to_domain') and auth['reply_to_domain'] != parsed.get('from_domain'):
        rt_id = f"domain:{auth['reply_to_domain']}"
        add_node(rt_id, auth['reply_to_domain'], 'domain', 'high')
        add_edge(email_id, rt_id, 'reply-to (mismatch)')

    geo_by_ip = {g['ip']: g for g in geo}
    for hop in relay_hops:
        if not hop.get('ip'):
            continue
        ip_id = f"ip:{hop['ip']}"
        risk = 'high' if hop.get('suspicious') else ('medium' if hop.get('is_origin') else 'low')
        add_node(ip_id, hop['ip'], 'ip', risk, {'hop_index': hop['hop_index']})
        if hop.get('is_origin'):
            add_edge(ip_id, domain_id, 'originated from')
        else:
            add_edge(ip_id, domain_id, f"relay hop #{hop['hop_index']}")

        g = geo_by_ip.get(hop['ip'])
        if g:
            loc_id = f"location:{g['country_code']}:{g['city']}"
            add_node(loc_id, f"{g['city']}, {g['country']}", 'location', risk)
            add_edge(ip_id, loc_id, 'located in')

    for ioc in iocs:
        if ioc['type'] == 'url':
            url_id = f"url:{ioc['value']}"
            add_node(url_id, ioc['value'][:60] + ('…' if len(ioc['value']) > 60 else ''), 'url', ioc['risk'])
            add_edge(email_id, url_id, 'contains link')

    recipient_id = f"recipient:{','.join(parsed.get('to_list', [])) or 'unknown'}"
    add_node(recipient_id, ', '.join(parsed.get('to_list', [])) or 'Unknown recipient', 'recipient', 'low')
    add_edge(email_id, recipient_id, 'delivered to')

    return {'nodes': nodes, 'edges': edges}
