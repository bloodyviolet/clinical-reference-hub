"""Backward-compatible entry point for SAE/NANDA seeding.

Kept so existing deployment commands continue to work. The authoritative
bilingual dataset is seeded transactionally by seed_sae.py.
"""
from seed_sae import seed_database


if __name__ == "__main__":
    seed_database()
