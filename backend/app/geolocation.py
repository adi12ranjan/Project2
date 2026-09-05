"""
geolocation.py — IP geolocation intelligence.

No external geolocation API is called (this must work fully offline, per the
spec). Instead we ship a small deterministic lookup table covering the demo
IP ranges, and any IP not in the table gets a clearly-labeled simulated
location derived deterministically from the IP itself (same IP always maps
to the same fake-but-plausible location — good enough for a demo map, never
presented as real intelligence).
"""
import hashlib

# Real-world-plausible demo entries for the IPs used in demo1-4.eml.
# Labeled 'source': 'demo_dataset' so the frontend can show "Demo data".
KNOWN_DEMO_IPS = {
    '45.153.160.140': {'country': 'Netherlands', 'country_code': 'NL', 'city': 'Amsterdam',
                        'isp': 'Frantech Solutions (bulletproof hosting)', 'asn': 'AS53667', 'lat': 52.3676, 'lon': 4.9041},
    '185.220.101.47': {'country': 'Germany', 'country_code': 'DE', 'city': 'Frankfurt',
                        'isp': 'Known Tor exit relay range', 'asn': 'AS204800', 'lat': 50.1109, 'lon': 8.6821},
    '104.18.32.77':   {'country': 'United States', 'country_code': 'US', 'city': 'San Francisco',
                        'isp': 'Corporate mail relay (acmecorp)', 'asn': 'AS13335', 'lat': 37.7749, 'lon': -122.4194},
    '193.29.107.62':  {'country': 'Bulgaria', 'country_code': 'BG', 'city': 'Sofia',
                        'isp': 'Fast Serv Inc (offshore hosting)', 'asn': 'AS62240', 'lat': 42.6977, 'lon': 23.3219},
    '104.16.20.88':   {'country': 'United States', 'country_code': 'US', 'city': 'Austin',
                        'isp': 'Corporate mail server (brightwave-tech)', 'asn': 'AS13335', 'lat': 30.2672, 'lon': -97.7431},
    '104.16.20.91':   {'country': 'United States', 'country_code': 'US', 'city': 'Austin',
                        'isp': 'Corporate mail server (brightwave-tech)', 'asn': 'AS13335', 'lat': 30.2672, 'lon': -97.7431},
    '178.128.44.19':  {'country': 'Singapore', 'country_code': 'SG', 'city': 'Singapore',
                        'isp': 'DigitalOcean (cloud VPS)', 'asn': 'AS14061', 'lat': 1.3521, 'lon': 103.8198},
}

_DEMO_CITIES = [
    ('United States', 'US', 'Ashburn', 39.0438, -77.4874),
    ('Russia', 'RU', 'Moscow', 55.7558, 37.6173),
    ('China', 'CN', 'Shenzhen', 22.5431, 114.0579),
    ('Brazil', 'BR', 'Sao Paulo', -23.5505, -46.6333),
    ('Nigeria', 'NG', 'Lagos', 6.5244, 3.3792),
    ('Vietnam', 'VN', 'Hanoi', 21.0278, 105.8342),
    ('Ukraine', 'UA', 'Kyiv', 50.4501, 30.5234),
    ('India', 'IN', 'Mumbai', 19.0760, 72.8777),
]


def geolocate_ip(ip: str) -> dict:
    if ip in KNOWN_DEMO_IPS:
        entry = dict(KNOWN_DEMO_IPS[ip])
        entry['ip'] = ip
        entry['source'] = 'demo_dataset'
        return entry

    # Deterministic pseudo-location for any other IP, clearly labeled simulated.
    h = int(hashlib.sha256(ip.encode()).hexdigest(), 16)
    country, cc, city, lat, lon = _DEMO_CITIES[h % len(_DEMO_CITIES)]
    jitter = ((h // len(_DEMO_CITIES)) % 200 - 100) / 100.0  # +/-1.0 degree jitter, deterministic
    return {
        'ip': ip, 'country': country, 'country_code': cc, 'city': city,
        'isp': 'Unknown (simulated demo data)', 'asn': 'AS00000',
        'lat': round(lat + jitter, 4), 'lon': round(lon + jitter, 4),
        'source': 'simulated_demo',
    }


def geolocate_all(ips: list) -> list:
    seen = set()
    out = []
    for ip in ips:
        if ip in seen:
            continue
        seen.add(ip)
        out.append(geolocate_ip(ip))
    return out
