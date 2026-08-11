from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import CustomerStatus, OpportunityStage, PromiseStatus, SaleStatus


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
    active: bool


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    role: str = "sales"


class UserUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    role: str
    active: bool


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10, max_length=128)


class AdminPasswordReset(BaseModel):
    new_password: str = Field(min_length=10, max_length=128)


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


class ActivityIn(BaseModel):
    activity_type: str = "note"
    description: str = Field(min_length=2, max_length=2000)
    follow_up_date: date | None = None


class ActivityOut(ActivityIn, ORMModel):
    id: int
    customer_id: int
    user_name: str
    created_at: datetime


class CustomerFileOut(ORMModel):
    id: int
    customer_id: int
    original_name: str
    content_type: str
    size: int
    description: str | None
    user_name: str
    created_at: datetime


class CustomerDetail(CustomerOut):
    sales: list[SaleOut]
    activities: list[ActivityOut]
    files: list[CustomerFileOut]


class OwnerAssignment(BaseModel):
    user_id: int


class OpportunityIn(BaseModel):
    customer_id: int
    owner_id: int
    title: str = Field(min_length=2, max_length=220)
    amount: Decimal = Field(ge=0)
    stage: OpportunityStage = OpportunityStage.new
    next_action: str | None = None
    next_action_date: date | None = None
    notes: str | None = None


class OpportunityOut(OpportunityIn, ORMModel):
    id: int
    customer_name: str
    owner_name: str
    created_at: datetime
    updated_at: datetime


class CustomerOwnerOut(BaseModel):
    customer_id: int
    user_id: int
    user_name: str


class ReportSummary(BaseModel):
    sales: Decimal
    collected: Decimal
    receivable: Decimal
    overdue: Decimal
    opportunities: Decimal
    won_opportunities: Decimal
    customers: int


class ReceivableRow(BaseModel):
    customer_id: int
    customer_name: str
    phone: str
    total: Decimal
    paid: Decimal
    balance: Decimal
    oldest_due_date: date | None
    days_overdue: int
    aging_bucket: str


class AuditLogOut(ORMModel):
    id: int
    user_id: int
    user_name: str
    action: str
    entity_type: str
    entity_id: int | None
    description: str
    created_at: datetime


class DashboardOut(BaseModel):
    total_sales: Decimal
    total_collected: Decimal
    total_receivable: Decimal
    overdue: Decimal
    due_today: Decimal
    due_next_7_days: Decimal
    active_customers: int
    overdue_customers: int
