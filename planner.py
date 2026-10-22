"""Deterministic, offline planning. This is NOT a generative AI model."""
import re

STEPS={
 "nova":["Inspect website availability and recent repository changes","Identify suspected issue and collect evidence","Prepare an isolated fix proposal","Run tests and request approval before deployment"],
 "inventory":["Inspect inventory alerts and schedule (read-only)","Identify affected branches and dates","Prepare a discrepancy report","Request approval before modifying any live data"],
 "sap":["Validate SAP and iiko exports and mapping dictionary","Preserve article leading zeros and aggregate duplicate rows","Produce reconciliation report in sandbox","Send output for review, without changing source data"],
 "kinder":["Inspect specification using synthetic data only","Propose change in development workspace","Test permissions and session rules","Request approval before releasing changes"],
 "qualisift":["Review backlog and code status","Propose isolated implementation","Run offline tests","Request approval before deployment"]
}
RISK_WORDS=re.compile(r"\b(delete|destroy|drop|deploy|publish|payment|refund|удали|удалить|оплат|платеж|публикуй|запусти в прод|разверни)\b",re.I)
def plan(project, description):
    if project not in STEPS: raise ValueError("unknown project")
    if not description.strip(): raise ValueError("empty task")
    risky=bool(RISK_WORDS.search(description))
    return {
        "project":project,
        "request":description[:1000],
        "risk":"approval_required" if risky else "review_before_execution",
        "steps":STEPS[project],
        "execution_enabled":False,
        "model":"offline_rules_v1"
    }
def format_plan(value):
    lines=[f"Plan: {value['project']}",f"Risk: {value['risk']}","Mode: preparation only, no execution"]
    lines.extend(f"{i}. {step}" for i,step in enumerate(value["steps"],1))
    return "\n".join(lines)
