# Empower orchestrator

<!-- EMPOWER_ORCHESTRATOR:START -->

Factory automation is allowed only when the operator can still understand and recover from what is about to happen.
Before dispatching automation or creating a durable system change, state the four-question blast-radius check:

1. **Scale** — how many repositories, files, jobs, runners, users, or environments can this touch?
2. **Severity** — what is the worst plausible breakage if this is wrong?
3. **Reversibility** — how quickly can the operator roll it back or stop it?
4. **Predictability** — is the system deterministic enough to trust unattended execution?

If any answer is unclear, narrow the action, add a dry run, or require explicit operator confirmation before continuing.

<!-- EMPOWER_ORCHESTRATOR:END -->

Installation-specific source paths, machine names, private network labels, and repository handles are intentionally omitted from the product repo. Keep local recipe paths in ignored instance notes.
