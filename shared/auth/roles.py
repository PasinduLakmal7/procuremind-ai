"""Standard Role Definitions for the Procurement Intelligence Platform."""
from enum import Enum


class SystemRole(str, Enum):
    ADMIN = "admin"
    PROCUREMENT_MANAGER = "procurement_manager"
    PROCUREMENT_OFFICER = "procurement_officer"
    SUPPLY_CHAIN_ANALYST = "supply_chain_analyst"
    AUDITOR = "auditor"


ALL_ROLES = [role.value for role in SystemRole]

