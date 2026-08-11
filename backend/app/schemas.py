from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import CustomerStatus, PromiseStatus, SaleStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORMModel):
    id: int
    name: str
    email: str
    role: str


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class CustomerIn(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    company: str | None = None
    phone: str = Field(min_length=10, max_length=30)
    email: EmailStr | None = None
    status: CustomerStatus = CustomerStatus.prospect
    notes: str | None = None
    next_follow_up: date | None = None


class CustomerOut(CustomerIn, ORMModel):
    id: int
    created_at: datetime
    balance: Decimal = Decimal("0")


class ProductIn(BaseModel):
    name: str
    category: str = "Servicio"
    price: Decimal = Decimal("0")
    active: bool = True


class ProductOut(ProductIn, ORMModel):
    id: int


class SaleIn(BaseModel):
    customer_id: int
    product_id: int | None = None
    concept: str
    vehicle: str | None = None
    amount: Decimal = Field(gt=0)
    status: SaleStatus = SaleStatus.won
    sale_date: date = Field(default_factory=date.today)
    notes: str | None = None


class SaleOut(SaleIn, ORMModel):
    id: int
    customer_name: str
    paid: Decimal
    balance: Decimal


class PaymentIn(BaseModel):
    sale_id: int
    amount: Decimal = Field(gt=0)
    paid_at: date = Field(default_factory=date.today)
    method: str = "Transferencia"
    reference: str | None = None
    notes: str | None = None


class PaymentOut(PaymentIn, ORMModel):
    id: int


class PromiseIn(BaseModel):
    sale_id: int
    amount: Decimal = Field(gt=0)
    due_date: date
    status: PromiseStatus = PromiseStatus.pending
    notes: str | None = None


class PromiseOut(PromiseIn, ORMModel):
    id: int
    customer_name: str
    concept: str
    days_overdue: int


class DashboardOut(BaseModel):
    total_sales: Decimal
    total_collected: Decimal
    total_receivable: Decimal
    overdue: Decimal
    due_today: Decimal
    due_next_7_days: Decimal
    active_customers: int
    overdue_customers: int
