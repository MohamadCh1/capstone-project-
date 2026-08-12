import os
from decimal import Decimal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def to_serializable(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)
