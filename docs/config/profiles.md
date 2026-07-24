# Runtime profiles

ForgeMind uses **profiles** to package budgets, permissions, path rules, and approval triggers.

| Profile | Intent |
|---------|--------|
| `readonly` | Explore / explain — read-only repo + git read |
| `standard` | Default engineering — write + tests; git/remote mutations gated |
| `strict` | Cautious — writes/exec also require approval; tighter budgets |

Example files: [`../../configs/`](../../configs/)

---

## Loading precedence

```text
defaults (profile) → config file → environment → CLI/programmatic overrides
```

```python
from forgemind.config import load_config, AgentProfile

cfg = load_config(
    profile=AgentProfile.STANDARD,
    config_file="configs/standard.toml",
    overrides={"budgets": {"max_steps": 20}},
)
```

### Environment variables

| Variable | Maps to |
|----------|---------|
| `FORGEMIND_PROFILE` | `profile` |
| `FORGEMIND_LOG_LEVEL` | `log_level` |
| `FORGEMIND_REQUIRE_REVIEW_BEFORE_COMPLETION` | `require_review_before_completion` |
| `FORGEMIND_MAX_STEPS` | `budgets.max_steps` |
| `FORGEMIND_MAX_TOOL_CALLS` | `budgets.max_tool_calls` |
| `FORGEMIND_MAX_REPAIR_ITERATIONS` | `budgets.max_repair_iterations` |
| `FORGEMIND_TIMEOUT_SECONDS` | `budgets.timeout_seconds` |
| `FORGEMIND_MAX_COST_USD` | `budgets.max_cost_usd` |
| `FORGEMIND_PERMISSIONS` | `policy.permissions` (comma-separated) |
| `FORGEMIND_MODEL` | `provider.model` |
| `FORGEMIND_TEMPERATURE` | `provider.temperature` |
| `FORGEMIND_MAX_TOKENS` | `provider.max_tokens` |
| `FORGEMIND_BASE_URL` | `provider.base_url` |

Supported file formats: **TOML** and **JSON**.

---

## Profile comparison

| Capability | readonly | standard | strict |
|------------|:--------:|:--------:|:------:|
| `repo.read` | yes | yes | yes |
| `repo.write` | no | yes | yes |
| `test.run` | no | yes | yes |
| `git.read` | yes | yes | yes |
| `git.write` / `github.*` | no | no* | no* |
| Write risk needs approval | n/a (denied) | no | **yes** |
| Exec / test risk needs approval | n/a | no | **yes** |
| Git / remote mutation approval | if ever granted | **yes** | **yes** |
| Lockfile / `pyproject.toml` write approval | — | **yes** | **yes** |
| Default max steps | 40 | 50 | 30 |
| Repair iterations | 0 | 5 | 2 |
| Cost cap | none | none | $5 |

\* Permissions are not granted by default; if added later, risk class still requires approval.

---

## Policy engine

```python
from forgemind.config import profile_config
from forgemind.policy import PolicyEngine, PolicyRequest
from forgemind.core.enums import Permission, RiskClass

engine = PolicyEngine.from_config(
    profile_config("standard"),
    workspace_root=".",
)

decision = engine.authorize(
    PolicyRequest(
        permissions=[Permission.REPO_WRITE],
        risk_class=RiskClass.WRITE,
        path="src/app.py",
    )
)
# decision.allowed / decision.requires_approval
```

Rules evaluated in order:

1. Required permissions must be present  
2. Path must stay inside workspace (jail)  
3. Path denylist / allowlist  
4. Approval flags from risk class, tool hint, or sensitive path globs  

Denied checks raise `PermissionDeniedError` via `authorize()` (or return `allowed=False` via `evaluate()`).

Default denylist includes `.env`, secrets globs, key material, and `.git/objects/**`.

---

## Budgets

```python
from forgemind.config import assert_step_budget

counters = cfg.budgets.to_counters()
assert_step_budget(counters)  # raises BudgetExceededError when exhausted
```

Caps covered: steps, tool calls, repair iterations, optional USD cost. Wall-clock `timeout_seconds` is stored for the orchestrator (Phase 6) to enforce.
