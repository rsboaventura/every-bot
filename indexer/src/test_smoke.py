import os, json
from .crawl_site import crawl  # type: ignore[attr-defined]
from .build_index import build  # type: ignore[attr-defined]
from .config import settings  # type: ignore[attr-defined]

def test_crawl_and_build_monkeypatch(monkeypatch):  # type: ignore[no-untyped-def]
	# force offline embeddings
	monkeypatch.setenv('OFFLINE_EMBED','1')
	# monkeypatch crawl to avoid real network
	def fake_crawl():
		return [
			{'title':'Home','url': settings.BASE_URL, 'text':'Bem vindo à Every plataforma AI.'},
			{'title':'Sobre','url': settings.BASE_URL + '/sobre', 'text':'Nossa missão é impulsionar produtividade.'}
		]
	monkeypatch.setattr('indexer.src.crawl_site.crawl', fake_crawl)
	docs = fake_crawl()
	build(docs, 'rebuild')
	out_dir = settings.OUT_DIR
	assert os.path.exists(out_dir)
	with open(os.path.join(out_dir,'meta.json'),'r') as f:
		meta = json.load(f)
	assert len(meta) > 0
