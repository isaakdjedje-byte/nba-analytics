# Format de message inter-sessions

Tous les echanges copies/colles entre sessions doivent respecter ce format.

```text
[MSG_ID] ORCH-YYYYMMDD-001
[FROM] ORCH|A|B|C
[TO] ORCH|A|B|C
[TYPE] TASK|INFO|BLOCKER|HANDOFF|ACK|DECISION
[PRIORITY] P1|P2|P3
[SUBJECT] titre court
[BODY]
- point 1
- point 2
[ACTION_REQUIRED] oui|non
[DEADLINE] YYYY-MM-DD HH:MM
[RESPONSE_FORMAT]
- STATUS:
- CURRENT_GATE:
- EVIDENCE:
- BLOCKERS:
```

## Exemples

### 1) Handoff A vers C
```text
[MSG_ID] A-20260210-014
[FROM] A
[TO] C
[TYPE] HANDOFF
[PRIORITY] P1
[SUBJECT] GATE_A1 pret - contrat API v1
[BODY]
- endpoints finaux: ...
- endpoints deprecies: ...
- payload examples: ...
[ACTION_REQUIRED] oui
[DEADLINE] 2026-02-10 18:00
[RESPONSE_FORMAT]
- STATUS:
- ACK:
- ETA adaptation:
```

### 2) Blocker B vers ORCH
```text
[MSG_ID] B-20260210-021
[FROM] B
[TO] ORCH
[TYPE] BLOCKER
[PRIORITY] P1
[SUBJECT] blocage fusion scripts backtest
[BODY]
- cause: ...
- impact: ...
- action requise: ...
[ACTION_REQUIRED] oui
[DEADLINE] 2026-02-10 15:00
[RESPONSE_FORMAT]
- DECISION:
- OWNER:
- ETA:
```

### 3) ACK C vers A
```text
[MSG_ID] C-20260210-011
[FROM] C
[TO] A
[TYPE] ACK
[PRIORITY] P2
[SUBJECT] recu GATE_A1
[BODY]
- contrat API pris en compte
- questions: ...
- ETA alignement frontend: ...
[ACTION_REQUIRED] non
[DEADLINE] 2026-02-10 20:00
[RESPONSE_FORMAT]
- STATUS:
```
