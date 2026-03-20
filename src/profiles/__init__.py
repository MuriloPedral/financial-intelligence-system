# Reexporta as funcoes principais do modulo de perfis para facilitar os imports.
from src.profiles.account_profiles import build_account_profile_lookup, build_account_profiles

__all__ = ["build_account_profiles", "build_account_profile_lookup"]
