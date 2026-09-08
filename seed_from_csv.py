"""Backward-compatible entry point for the SAE CSV seeder.

The old version POSTed each row to an API endpoint that no longer exists.
This wrapper now uses the transactional local seeder instead.
"""
from seed_sae import seed_database


if __name__ == "__main__":
    seed_database()
