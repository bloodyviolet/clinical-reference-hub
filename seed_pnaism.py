"""Compatibility wrapper for older deployment commands.

PNAISM now lives in the unified public_health_policies table.
"""
from seed_policies import seed_policies


def seed_pnaism():
    return seed_policies({"PNAISM"})


if __name__ == "__main__":
    seed_pnaism()
