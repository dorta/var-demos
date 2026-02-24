#!/usr/bin/env python3
import json
from pathlib import Path

rows = []
for p in sorted(Path('results').glob('*.json')):
    data = json.loads(p.read_text())
    lat = data.get('latency_ms', {})
    rows.append((p.stem, data.get('delegate', ''), lat.get('avg', 0.0), lat.get('p50', 0.0), lat.get('p90', 0.0), lat.get('p99', 0.0)))

print('name,delegate,avg_ms,p50_ms,p90_ms,p99_ms')
for r in rows:
    print(f'{r[0]},{r[1]},{r[2]:.3f},{r[3]:.3f},{r[4]:.3f},{r[5]:.3f}')
