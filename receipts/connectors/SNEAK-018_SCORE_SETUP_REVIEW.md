# SNEAK-018 Javier app-security-score setup + requirements review

- Breakpoint root: `9e86cb2869917d62e027227adf31621e65b2aaf03b784fe9dc41417e24ba2327`
- Review package digest: `c6f72fa94d0666740f03f5bf80f5b77e9215e4adf73879d086602570a50dacbc`
- BAND hashed message leaf: `e070f2fdf648602f718d07416f10e78de57168918f37ec4841f13cad95ac91dc`
- BAND hashed message root: `e070f2fdf648602f718d07416f10e78de57168918f37ec4841f13cad95ac91dc`
- Javier pin: `6e1f27605fe278eed347b10dab6f39b3501f1486` match=True node_match=True
- Tool score scale: **0–10** (10 = clean; **0 = worst**, many findings)
- Event Snyk bonus: up to **+10%** → **NOT_AWARDED** (needs live SCA/SAST)
- Live Snyk: **NOT_TESTED** (SNYK_TOKEN missing)
- Application score: **null** (coverage incomplete — correctly rejected)
- AoK entry_gate: **False** (0/30)
- Cognee @Data: **PASS** receipt `data_breakpoint-77974f1c1959`
- BAND review request: **PASS**

## Clarification
Forcing tool score to 0 does **not** earn the extra ten marks. The bonus path is real Snyk integration + clean coverage toward **10/10**, and judges separately may award up to +10%.
