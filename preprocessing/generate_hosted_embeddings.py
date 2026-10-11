import sys,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from pipeline import get_client,load_character_data
catalog_path=root/'web/data/characters.json'
characters=load_character_data(catalog_path)
texts=['角色: '+c['name']+'。萌點描述: '+', '.join(c['moe_traits'])+'。' for c in characters]
response=get_client().embeddings.create(model='text-embedding-3-small',input=texts,dimensions=1024)
vectors=[item.embedding for item in sorted(response.data,key=lambda x:x.index)]
assert len(vectors)==len(characters) and all(len(v)==1024 for v in vectors)
data={'model':'text-embedding-3-small','dimensions':1024,'catalog_sha256':hashlib.sha256(catalog_path.read_bytes()).hexdigest(),'characters':characters,'vectors':vectors}
(root/'web/data/index.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print('Hosted index generated:',len(vectors),'characters; dimensions: 1024')
