# Prompt: review a ForgeMind PR

```text
Review this ForgeMind change as a senior maintainer.

Check:
1. Is it scoped to a single roadmap phase (or clearly labeled otherwise)?
2. Does it avoid forward-dependencies on later phases?
3. Are public APIs minimal and typed?
4. Are tests meaningful (no network in unit tests)?
5. Were docs / ROADMAP updated if exit criteria moved?
6. Any security concerns around tools, plugins, or secrets?

Do not suggest implementing unfinished future phases unless required to unblock.
Return: findings first (ordered by severity), then residual risks, then a brief summary.
```
