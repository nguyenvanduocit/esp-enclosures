"""Build the static gallery from models.json; Python standard library only."""
import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build():
    models = json.loads((ROOT / 'models.json').read_text())
    cards = []
    ids = set()
    for model in models:
        model_id = model['id']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', model_id) or model_id in ids:
            raise ValueError(f'Invalid or duplicate model id: {model_id}')
        ids.add(model_id)
        for key in ('thumbnail', 'viewer', 'download'):
            path = (ROOT / model[key]).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file():
                raise ValueError(f'{model_id}: missing local {key}: {model[key]}')
        value = {key: escape(str(item), quote=True) for key, item in model.items()}
        cards.append(f'''<article class="card" data-id="{value['id']}">
  <a class="model-link" href="{value['viewer']}" aria-labelledby="title-{value['id']}">
    <div class="thumbnail"><img src="{value['thumbnail']}" alt="Mô hình {value['title']} khi tách nắp" width="960" height="720" loading="lazy"><span class="open-label">Xem 3D ↗</span></div>
    <div class="card-body"><p class="category">{value['category']}</p><h2 id="title-{value['id']}">{value['title']}</h2><p class="description">{value['description']}</p><p class="spec">{value['dimensions']}<span>{value['parts']} chi tiết</span></p></div>
  </a>
  <div class="card-footer"><span class="status">{value['status']}</span><a class="download" href="{value['download']}" download aria-label="Tải ZIP {value['title']}">Tải ZIP ↓</a></div>
</article>''')
    template = (ROOT / 'gallery-template.html').read_text()
    html = template.replace('__CARDS__', '\n'.join(cards)).replace('__COUNT__', str(len(cards)))
    (ROOT / 'index.html').write_text(html)
    print(f'Built index.html: {len(cards)} models')


if __name__ == '__main__':
    build()
