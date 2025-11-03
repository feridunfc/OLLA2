# multiai/core/ledger.py
"""
DEPRECATED: use multiai.core.ledger_signed.write_manifest_to_ledger
This file kept for backward compatibility with older endpoints.
"""
from .ledger_signed import write_manifest_to_ledger, get_conn  # re-export
