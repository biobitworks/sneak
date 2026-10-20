# Sneak security-demo (staged scan target)

Minimal first-party app built by the Sneak workflow for SCA/SAST binding.
This is a disposable demo target, not production Overwatch software.

## Build

```bash
python3 -m pip install -e apps/security-demo
python3 -m security_demo --check
```

Live Snyk scans require an operator-supplied `SNYK_TOKEN` outside the repo and
are recorded separately. Incomplete coverage cannot be reported as a clean score.
