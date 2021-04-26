from dataclasses import dataclass
from datetime import datetime


@dataclass
class BradescoTransaction:
    date: datetime
    description: str
    amount: float
