"""Baixa as fotos candidatas do Unsplash (Licença Unsplash, uso livre) e monta folhas de contato."""
import io, json, os
import requests
from PIL import Image, ImageDraw

OUT = '_fotos'
data = json.load(open(os.path.join(OUT, 'unsplash.json'), encoding='utf-8'))
os.makedirs(os.path.join(OUT, 'u'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'usheets'), exist_ok=True)
UA = {'User-Agent': 'convite-quarentou/1.0 (lista de presentes pessoal)'}
report = {}
for slug, lst in data.items():
    ok = []
    for i, (pid, page) in enumerate(lst):
        url = f'https://images.unsplash.com/{pid}?w=600&q=78&fm=jpg'
        try:
            r = requests.get(url, headers=UA, timeout=40)
            r.raise_for_status()
            im = Image.open(io.BytesIO(r.content)).convert('RGB')
            p = os.path.join(OUT, 'u', f'{slug}_{i}.jpg')
            im.save(p, quality=85)
            ok.append(i)
        except Exception as e:
            print('ERRO', slug, i, pid, e, flush=True)
    report[slug] = ok
    if ok:
        sheet = Image.new('RGB', (len(ok) * 250, 270), (20, 14, 10))
        d = ImageDraw.Draw(sheet)
        for k, i in enumerate(ok):
            im = Image.open(os.path.join(OUT, 'u', f'{slug}_{i}.jpg'))
            im.thumbnail((240, 240))
            sheet.paste(im, (k * 250 + 5, 5))
            d.rectangle([k * 250 + 5, 248, k * 250 + 40, 268], fill=(0, 0, 0))
            d.text((k * 250 + 10, 252), str(i), fill=(255, 220, 120))
        sheet.save(os.path.join(OUT, 'usheets', f'{slug}.jpg'), quality=80)
    print(slug, ok, flush=True)
json.dump(report, open(os.path.join(OUT, 'baixadas.json'), 'w'), indent=1)
