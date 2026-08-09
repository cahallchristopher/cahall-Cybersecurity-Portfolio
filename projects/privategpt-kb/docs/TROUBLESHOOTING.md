# Troubleshooting

---

## Error 1 -- Silent rm -rf Failure

Inner models/ directory was owned by root.
```bash
ls -la ~/private-gpt/models/
# drwxr-xr-x 3 root root 4096

sudo rm -rf ~/private-gpt
```

---

## Error 2 -- No such option: --settings

PrivateGPT v1.0.1 does not support --settings CLI flag.
Use environment variables instead:
```bash
export PGPT_LLM_DEFAULT=nous-hermes2:10.7b
private-gpt serve
```

---

## Error 3 -- Qdrant Embedded Mode Lock
RuntimeError: Storage folder .../qdrant is already accessed by another instance.
Patch built-in settings.yaml AND unset the variable:
```bash
sed -i "s|path: \${PGPT_QDRANT_PATH:local_data/qdrant}|path: \${PGPT_QDRANT_PATH:}|" settings.yaml
unset PGPT_QDRANT_PATH
```

---

## Error 5 -- Embedding Model Not Found
Must use full tag:
```bash
export PGPT_EMBEDDING_DEFAULT=mxbai-embed-large:latest
```

---

## Error 6 -- gRPC Port 6334 Refused

Expose both ports and disable gRPC:
```bash
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 ...
export PGPT_QDRANT_PREFER_GRPC=false
```

---

## Error 7 -- Ingest Returns 404

Introspect the API to find current endpoints:
```bash
curl -s http://localhost:8080/openapi.json | python3 -c "
import json, sys
api = json.load(sys.stdin)
for path in api['paths'].keys(): print(path)
"
```

---

## Error 8 -- JSON Decode Error

Shell $(cat file.txt) inlines literal newlines into JSON.
Use Python requests:
```python
with open("file.txt", "r") as f:
    content = f.read()
requests.post(url, json={"input": {"type": "text", "value": content}})
```

---

## Error 9 -- Port Already in Use

```bash
sudo fuser -k 8080/tcp
sleep 2
~/privategpt-data/start.sh
```
