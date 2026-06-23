from app.core.database import SessionLocal
from app.services.rag_service import search

db = SessionLocal()
try:
    hits = search(db, '应届生身份认定', top_k=3)
    print('检索结果:')
    for h in hits:
        did = h.get('document_id')
        print('  document_id={} (type={})'.format(did, type(did).__name__))
        print('  document_title={}'.format(h.get('document_title')))
        print('  content={}...'.format((h.get('content') or '')[:50]))
        print()
finally:
    db.close()
