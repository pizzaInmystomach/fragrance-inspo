#!/bin/bash
set -e
python - << 'PY'
from pathlib import Path
p=Path('app/ingest.py')
s=p.read_text()
old='for schema, vector in zip(schemas, embeddings):\n        doc = schema.to_lancedb_doc()\n        # 使用新的 embedding 欄位名稱（與 search_engine.py 一致）\n        doc["embedding"] = vector\n        table_records.append(doc)'
new='for schema, vector in zip(schemas, embeddings):\n        doc = schema.to_lancedb_doc()\n        # Convert to float32 numpy array so LanceDB treats as vector column\n        try:\n            vec32 = np.asarray(vector, dtype=np.float32)\n        except Exception:\n            vec32 = vector\n        doc["embedding"] = vec32\n        table_records.append(doc)'
if old in s:
    s=s.replace(old,new)
    s='import numpy as np\n'+s if 'import numpy as np' not in s else s
    p.write_text(s)
    print('patched')
else:
    print('pattern not found')
PY
