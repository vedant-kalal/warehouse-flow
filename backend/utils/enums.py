from enum import Enum


class OperationType(str, Enum):
    receipt = "receipt"
    delivery = "delivery"
    transfer = "transfer"
    adjustment = "adjustment"


class OperationStatus(str, Enum):
    draft = "draft"
    confirmed = "confirmed"
    done = "done"
    cancelled = "cancelled"


class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    staff = "staff"
