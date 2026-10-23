# Initial open-source agent comparison

Read-only research, 2026-10-22 UTC. No package or external agent was installed, no paid service
enabled, and no third-party program was given workspace/credential access.

| Candidate | Evidence inspected | Fit | Remaining checks |
| --- | --- | --- | --- |
| [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) | README and pyproject: Python >=3.10, MIT, agents/tools/handoffs, sessions, human review, sandbox and voice options | Strong candidate for model orchestration around the existing Python queue; do not replace the working coordinator | Pin a release, review transitive dependency licenses/advisories, disable unwanted tracing, benchmark, enforce budget gate; verify real sandbox boundaries |
| [OpenHands](https://github.com/OpenHands/OpenHands) | Current README and MIT license; current Canvas references software-agent-sdk, Docker backends, separate conversation workspaces, Node 24 in multi-sandbox setup | Candidate for an isolated coding executor after resource/security evaluation | Review the separately referenced SDK/server, image digests and dependencies; bound RAM/CPU; do not expose Docker socket or production workspaces |
| [LangGraph](https://github.com/langchain-ai/langgraph) | README: MIT badge, durable execution, checkpoints, human interrupts and memory | Useful durable orchestration component, but overlaps existing SQLite queue and approval state | Assess actual need before adding a second coordinator; dependency review and failure/recovery tests |

Source evidence blob IDs:

- OpenAI SDK README 40f490c110cd584f7034bd221c6da37379fc41ff.
- OpenAI SDK pyproject 3542d3c14c5fbf6475da79b6810de620213b9523.
- OpenHands README 081f47badceccf5abdcf8994c715627d58bbf4b0.
- OpenHands LICENSE f6f60f52368bcc96f82fbe59ec65049c2c3af9db.
- LangGraph README 97c31e9cb4d8fe56be8d768ce3eb5e22400e897e.

Recommendation for the next experiment: evaluate the OpenAI SDK as a bounded orchestrator and
compare a minimal isolated coding worker with the OpenHands SDK. This is a research direction,
not a completed security audit, resource benchmark or final integration decision. A same-user
local shell is not adequate isolation from Inventory. Keep shared-host production paths and
secrets outside any agent container and preserve owner approval for publication.
