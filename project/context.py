"""
Kisan Dost — Context (Root Forwarder)
Forwarding to context.farmer_context for backward compatibility.
"""

from context.farmer_context import FarmerContext, FarmerProfile  # noqa: F401

__all__ = ["FarmerContext", "FarmerProfile"]
