# SNEAK-017 MagicStudio / Ollama / Desktop Commander

- Chain root: `ea8c1cbd4919f26d68f6c9bf967fcb4b9621f7b07ea26e587369bbcb9f20b178`
- Cloud local hostname: `cursor` (is_magicstudio=False)
- Ollama on cloud VM: **False**
- Desktop Commander MCP in this cloud agent: **False**
- Expected MagicStudio device: `00925fd7-ab95-4c88-89a5-963739392fc2` / `magicSTUDIObox.local`
- BAND Claude/ChatGPT probe relay: **PASS**

## Operator / Desktop Commander next step

On MagicStudio via Desktop Commander, run:

```zsh
#!/bin/zsh
set -euo pipefail
echo "HOSTNAME=$(hostname)"
echo "UNAME=$(uname -a)"
command -v ollama >/dev/null && ollama list || echo "OLLAMA_CLI=MISSING"
curl -fsS --max-time 5 http://127.0.0.1:11434/api/tags | head -c 4000 || echo "OLLAMA_HTTP=DOWN"
for m in qwen2.5:0.5b qwen2.5:1.5b; do
  if ollama list 2>/dev/null | awk '{print $1}' | grep -qx "$m"; then
    out=$(ollama run "$m" "Reply with exactly: OLLAMA_OK" 2>/dev/null | tr -d '\n' | head -c 200 || true)
    echo "INFER_$m=$out"
  else
    echo "INFER_$m=NOT_INSTALLED"
  fi
done
command -v claude >/dev/null && echo "CLAUDE_CLI=$(command -v claude)" || echo "CLAUDE_CLI=MISSING"
command -v codex >/dev/null && echo "CODEX_CLI=$(command -v codex)" || echo "CODEX_CLI=MISSING"
```

Or: `python3 scripts/probe_magicstudio_ollama.py` on that host.
Paste non-secret stdout back into BAND; we will append a successor receipt.
