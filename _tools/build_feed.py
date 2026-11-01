# Build noodlepets.app/feed/feed.json from the CMS rows.
# usage: python3 build_feed.py <dir with items/*.json (+ optional meta/switches.json) from the CMS> <dir with downloaded assets> <site repo>
import json, os, re, sys, glob, shutil
rows_dir, asset_dir, site = sys.argv[1:4]
SCREENS = {'pets','room','dressup','playground','tv','coins','plus','book','space'}
os.makedirs(f'{site}/feed/img', exist_ok=True)
items, used = [], set()
rows = []
for f in glob.glob(f'{rows_dir}/items/*.json'):
    j = json.load(open(f)); d = j.get('data', j); d['_id'] = j.get('id') or os.path.basename(f)[:-5]; rows.append(d)
rows.sort(key=lambda d: (d.get('kind') != 'banner', d.get('order') or 0, d.get('at') or ''))
for d in rows:
    if not d.get('on') or d.get('kind') not in ('banner', 'notif') or not d.get('title'): continue
    go = {'type': 'screen', 'screen': d.get('screen') if d.get('screen') in SCREENS else 'pets'}
    if d.get('goType') == 'url':
        if not re.match(r'^https://[^\s"\'<>]+\.[^\s"\'<>]+$', d.get('url') or ''): sys.exit(f'bad url in {d["title"]}')
        go = {'type': 'url', 'url': d['url']}
    it = {'id': d['_id'], 'kind': d['kind'], 'title': d['title'][:40], 'text': (d.get('text') or '')[:120], 'go': go}
    if d['kind'] == 'banner':
        it.update(bg=d.get('bg') or '#FFD84D', ink=d.get('ink') or '#2B211C', start=d.get('start') or '', end=d.get('end') or '')
        if d.get('img'):
            src = [p for p in glob.glob(f'{asset_dir}/{d["img"]}*')]
            if not src: sys.exit(f'missing picture for {d["title"]}')
            ext = os.path.splitext(src[0])[1] or '.jpg'; name = d['img'] + ext
            shutil.copy(src[0], f'{site}/feed/img/{name}'); used.add(name)
            it['img'] = f'https://noodlepets.app/feed/img/{name}'; it['overlay'] = bool(d.get('overlay'))
    else:
        if not re.match(r'^\d{4}-\d\d-\d\dT\d\d:\d\d', d.get('at') or ''): continue
        it['at'] = d['at'][:16]
    items.append(it)
# The game's own banners the CMS can switch off (meta/switches row); missing = on
sw_file = f'{rows_dir}/meta/switches.json'
sw = {}
if os.path.exists(sw_file):
    j = json.load(open(sw_file)); sw = j.get('data', j)
switches = {'space': sw.get('space') is not False}
for p in glob.glob(f'{site}/feed/img/*'):
    if os.path.basename(p) not in used and os.path.basename(p) != '.keep': os.remove(p)
json.dump({'v': 1, 'switches': switches, 'items': items}, open(f'{site}/feed/feed.json', 'w'), indent=1, ensure_ascii=False)
print(len(items), 'items;', len(used), 'pictures; space banner', 'on' if switches['space'] else 'off')
