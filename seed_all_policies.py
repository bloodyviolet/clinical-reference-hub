"""Compatibility wrapper for older deployment commands.

Historically this script seeded every policy except PNAISM. The behaviour is
kept for compatibility; new deployments should run `python seed_policies.py`.
"""
from policy_data import POLICY_DATA
from seed_policies import seed_policies


def seed_all_policies():
    return seed_policies(set(POLICY_DATA) - {"PNAISM"})


if __name__ == "__main__":
    seed_all_policies()
