"""Busca fotos candidatas de uso livre para a lista de presentes.

Fonte principal: Unsplash (Licença Unsplash: uso livre, sem necessidade de permissão),
excluindo fotos Unsplash+ (pagas). Reserva: Openverse (CC0, domínio público, CC BY, CC BY-SA).
Para cada presente baixa até 8 miniaturas (400 px) e monta uma folha de contato numerada.
"""
import io, json, os, time
import requests
from PIL import Image, ImageDraw

OUT = '_fotos'
UA = {'User-Agent': 'convite-quarentou/1.0 (lista de presentes pessoal)', 'Accept': 'application/json'}
items = json.load(open(os.path.join(OUT, 'queries.json'), encoding='utf-8'))
os.makedirs(os.path.join(OUT, 'cand'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'sheets'), exist_ok=True)
report = {}

def unsplash(q):
    r = requests.get('https://unsplash.com/napi/search/photos',
                     params={'query': q, 'per_page': 20}, headers=UA, timeout=30)
    r.raise_for_status()
    out = []
    for p in r.json().get('results', []):
        small = p.get('urls', {}).get('small', '')
        if p.get('premium') or p.get('plus') or 'plus.unsplash.com' in small:
            continue
        out.append({'src': 'unsplash', 'id': p['id'], 'img': small,
                    'page': p.get('links', {}).get('html'), 'author': (p.get('user') or {}).get('name'),
                    'license': 'Unsplash License', 'alt': p.get('alt_description') or ''})
    return out

def openverse(q):
    r = requests.get('https://api.openverse.org/v1/images/',
                     params={'q': q, 'license': 'cc0,pdm,by,by-sa', 'category': 'photograph', 'page_size': 12},
                     headers=UA, timeout=30)
    r.raise_for_status()
    out = []
    for p in r.json().get('results', []):
        out.append({'src': 'openverse', 'id': p['id'], 'img': p.get('thumbnail') or p.get('url'),
                    'page': p.get('foreign_landing_url'), 'author': p.get('creator'),
                    'license': ('CC ' + p.get('license', '').upper() + ' ' + (p.get('license_version') or '')).strip(),
                    'alt': p.get('title') or ''})
    return out

for slug, q in items:
    cands, errs = [], []
    for fn in (unsplash, openverse):
        if len(cands) >= 8:
            break
        try:
            cands += fn(q)
        except Exception as e:
            errs.append(f'{fn.__name__}: {e}')
        time.sleep(1)
    keep = []
    for c in cands:
        if len(keep) >= 8:
            break
        try:
            r = requests.get(c['img'], headers={'User-Agent': UA['User-Agent']}, timeout=30)
            r.raise_for_status()
            im = Image.open(io.BytesIO(r.content)).convert('RGB')
            im.thumbnail((400, 400))
            n = len(keep)
            path = os.path.join(OUT, 'cand', f'{slug}_{n}.jpg')
            im.save(path, quality=82)
            c['file'] = path
            keep.append(c)
        except Exception as e:
            errs.append(f'download {c.get("id")}: {e}')
    report[slug] = {'query': q, 'candidates': keep, 'errors': errs}
    # folha de contato 4x2 com números
    if keep:
        W = 4 * 220
        sheet = Image.new('RGB', (W, 2 * 240), (20, 14, 10))
        d = ImageDraw.Draw(sheet)
        for i, c in enumerate(keep):
            im = Image.open(c['file'])
            im.thumbnail((210, 210))
            x, y = (i % 4) * 220 + 5, (i // 4) * 240 + 5
            sheet.paste(im, (x, y))
            d.rectangle([x, y + 212, x + 60, y + 232], fill=(0, 0, 0))
            d.text((x + 4, y + 214), f'{i} {c["src"][:2]}', fill=(255, 220, 120))
        sheet.save(os.path.join(OUT, 'sheets', f'{slug}.jpg'), quality=80)
    print(slug, len(keep), errs[:2], flush=True)

json.dump(report, open(os.path.join(OUT, 'candidatas.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
