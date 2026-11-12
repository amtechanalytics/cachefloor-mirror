"""Regenerate the paper's tables from per_call.csv (standard library only).
Usage: python3 reproduce.py  -> prints Tables III (campaigns), IV (models), generations, ledger audit and headline numbers.
The cache-gap sensitivity grid (Table V) needs request text that is not released; its results are in sensitivity_cache_gap.csv."""
import csv, json, collections as C

rows = list(csv.DictReader(open('per_call.csv')))
S = json.load(open('price_sheet.json'))
P = {m: (v['input'], v['cache_read'], v['cache_write'], v['output']) for m, v in S['prices_usd_per_million'].items()}
for r in rows:
    for k in ('input_uncached', 'cache_read', 'cache_write', 'output', 'ok', 'retry', 'batch', 'interactive', 'tokens_logged'):
        r[k] = int(r[k])
    r['usd'] = float(r['cost_sheet_usd'])
    r['tin'] = r['input_uncached'] + r['cache_read'] + r['cache_write']
    r['ach'] = int(r['ach_cache_tokens']) if r['ach_cache_tokens'] != '' else None
    r['parse_fail'] = r['parse_ok'] == '0'

TOT = sum(r['usd'] for r in rows)
camps = sorted({r['campaign'] for r in rows}, key=lambda c: int(c[1:]))

def batch_eligible(r):
    return (r['phase'] == 'prod' and r['ok'] and not r['batch'] and not r['interactive']
            and r['vendor'] in ('Anthropic', 'OpenAI') and r['model'] in P)

def gap(r):
    if r['ach'] is None or r['model'] not in P:
        return 0.0
    pi, pr, pw, po = P[r['model']]
    return max(0, r['ach'] - r['cache_read']) * (pi - pr) / 1e6 * (0.5 if r['batch'] else 1.0)

def ceiling(r):
    if r['model'] not in P:
        return 0.0
    pi, pr, pw, po = P[r['model']]
    return r['input_uncached'] * (pi - pr) / 1e6 * (0.5 if r['batch'] else 1.0)

print('Campaigns (Table III)')
print('ID  calls   spend   gate%  rework%  cache_real%  gap$   ceiling$  batch_avoid%')
for c in camps:
    q = [r for r in rows if r['campaign'] == c]
    usd = sum(r['usd'] for r in q)
    gate = sum(r['usd'] for r in q if r['phase'] == 'gate')
    rework = sum(r['usd'] for r in q if r['phase'] == 'aborted' or r['retry'] or r['parse_fail'])
    tin = sum(r['tin'] for r in q); cr = sum(r['cache_read'] for r in q)
    real = 100 * cr / tin if (tin and all(r['tokens_logged'] for r in q)) else float('nan')
    print(f"{c:4}{len(q):6} {usd:8.2f} {100*gate/usd:6.1f} {100*rework/usd:7.1f} {real:11.1f} {sum(gap(r) for r in q):6.2f} {sum(ceiling(r) for r in q):8.2f} {100*sum(0.5*r['usd'] for r in q if batch_eligible(r))/usd:11.1f}")
print(f"All {len(rows)} {TOT:.2f}")

print('\nHeadline')
print('gates %.1f%%  rework %.1f%%  cache gap $%.2f (%.1f%%)  batch-eligible $%.2f (%.1f%%)  ceiling $%.2f (%.1f%%)  interactive $%.2f' % (
    100 * sum(r['usd'] for r in rows if r['phase'] == 'gate') / TOT,
    100 * sum(r['usd'] for r in rows if r['phase'] == 'aborted' or r['retry'] or r['parse_fail']) / TOT,
    sum(gap(r) for r in rows), 100 * sum(gap(r) for r in rows) / TOT,
    sum(0.5 * r['usd'] for r in rows if batch_eligible(r)), 100 * sum(0.5 * r['usd'] for r in rows if batch_eligible(r)) / TOT,
    sum(ceiling(r) for r in rows), 100 * sum(ceiling(r) for r in rows) / TOT,
    sum(r['usd'] for r in rows if r['interactive'])))
out = sum(r['output'] * P[r['model']][3] / 1e6 * (0.5 if r['batch'] else 1) for r in rows if r['model'] in P)
inp = sum((r['input_uncached'] * P[r['model']][0] + r['cache_read'] * P[r['model']][1] + r['cache_write'] * P[r['model']][2]) / 1e6 * (0.5 if r['batch'] else 1) for r in rows if r['model'] in P)
print('output share of priced spend %.1f%%' % (100 * out / (out + inp)))

print('\nBy generation')
for g in ('G1', 'G2', 'G3'):
    q = [r for r in rows if r['generation'] == g]; usd = sum(r['usd'] for r in q)
    print(g, len(q), round(usd, 2), 'batch %.1f%%' % (100 * sum(r['usd'] for r in q if r['batch']) / usd))

print('\nBy model (Table IV)')
pm = C.defaultdict(list)
for r in rows: pm[r['model']].append(r)
for m, q in sorted(pm.items(), key=lambda kv: -sum(r['usd'] for r in kv[1])):
    print(f"{m or '(none)':28} calls {len(q):6}  spend {sum(r['usd'] for r in q):7.2f}")

print('\nLedger audit (logged vs sheet, calls with a logged cost)')
for c in camps:
    q = [r for r in rows if r['campaign'] == c and r['cost_logged_usd'] != '' and r['model'] in P]
    if q:
        lg = sum(float(r['cost_logged_usd']) for r in q); sh = sum(r['usd'] for r in q)
        print(c, round(lg, 2), round(sh, 2), round(lg / sh, 3) if sh else None)
