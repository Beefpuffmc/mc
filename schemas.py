from pydantic import BaseModel
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True  # Позволяет создавать объекты из SQLAlchemy моделей

class WalletOut(BaseModel):
    id: int
    address: str
    private_key: str

    class Config:
        from_attributes = True

class TransactionCreate(BaseModel):
    recipient_address: str
    amount: float  # Изменено с int на float для поддержки дробных значений

class TransactionOut(BaseModel):
    id: int
    sender: str
    recipient: str
    amount: float  # Изменено с int на float для соответствия базе данных и логике
    timestamp: datetime

    class Config:
        from_attributes = True
