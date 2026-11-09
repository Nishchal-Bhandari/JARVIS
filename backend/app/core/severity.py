"""Severity P1-P4 (specsheet §8). Pure function."""


def compute_severity(impact: dict) -> str:
    n_services = len(impact.get("affected_services", []))
    users = impact.get("users_affected", 0)
    if impact.get("critical_path_hit") and (n_services >= 4 or users >= 50):
        return "P1"
    if impact.get("critical_path_hit"):
        return "P2"
    if n_services >= 2:
        return "P3"
    return "P4"
