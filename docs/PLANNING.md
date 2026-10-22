# Offline planning stage
The `/plan <project> <task>` command creates a deterministic, non-executing checklist. This feature is **not** an LLM and never changes code, production systems or other repositories.

It is intended as a secure first step toward an AI executor. For a real AI system, connect an explicitly approved model provider with limits and secret management, add an isolated execution runtime and mandatory action approval bound to immutable code commits, then verify with CI.
