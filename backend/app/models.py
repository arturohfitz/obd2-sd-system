import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class CustomerStatus(str, enum.Enum):
    prospect = "prospect"
    active = "active"
    inactive = "inactive"


class SaleStatus(str, enum.Enum):
    quote = "quote"
    negotiation = "negotiation"
    won = "won"
    lost = "lost"
    cancelled = "cancelled"


class PromiseStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    cancelled = "cancelled"


class OpportunityStage(str, enum.Enum):
    new = "new"
    contacted = "contacted"
    qualified = "qualified"
    quoted = "quoted"
    negotiation = "negotiation"
    won = "won"
    lost = "lost"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="admin")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    company: Mapped[str | None] = mapped_column(String(180))
    phone: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(180))
    status: Mapped[CustomerStatus] = mapped_column(Enum(CustomerStatus), default=CustomerStatus.prospect)
    notes: Mapped[str | None] = mapped_column(Text)
    next_follow_up: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    sales: Mapped[list["Sale"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    activities: Mapped[list["CustomerActivity"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    files: Mapped[list["CustomerFile"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), unique=True)
    category: Mapped[str] = mapped_column(String(80), default="Servicio")
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Sale(Base):
    __tablename__ = "sales"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    concept: Mapped[str] = mapped_column(String(220))
    vehicle: Mapped[str | None] = mapped_column(String(160))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[SaleStatus] = mapped_column(Enum(SaleStatus), default=SaleStatus.won)
    sale_date: Mapped[date] = mapped_column(Date, default=date.today)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    customer: Mapped[Customer] = relationship(back_populates="sales")
    product: Mapped[Product | None] = relationship()
    payments: Mapped[list["Payment"]] = relationship(back_populates="sale", cascade="all, delete-orphan")
    promises: Mapped[list["PaymentPromise"]] = relationship(back_populates="sale", cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    paid_at: Mapped[date] = mapped_column(Date, default=date.today)
    method: Mapped[str] = mapped_column(String(50), default="Transferencia")
    reference: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)
    sale: Mapped[Sale] = relationship(back_populates="payments")


class PaymentPromise(Base):
    __tablename__ = "payment_promises"
    id: Mapped[int] = mapped_column(primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    due_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[PromiseStatus] = mapped_column(Enum(PromiseStatus), default=PromiseStatus.pending)
    notes: Mapped[str | None] = mapped_column(Text)
    sale: Mapped[Sale] = relationship(back_populates="promises")


class CustomerActivity(Base):
    __tablename__ = "customer_activities"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    activity_type: Mapped[str] = mapped_column(String(40), default="note")
    description: Mapped[str] = mapped_column(Text)
    follow_up_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    customer: Mapped[Customer] = relationship(back_populates="activities")
    user: Mapped[User] = relationship()


class CustomerFile(Base):
    __tablename__ = "customer_files"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    original_name: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255), unique=True)
    content_type: Mapped[str] = mapped_column(String(120))
    size: Mapped[int] = mapped_column()
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    customer: Mapped[Customer] = relationship(back_populates="files")
    user: Mapped[User] = relationship()


class CustomerOwner(Base):
    __tablename__ = "customer_owners"
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    customer: Mapped[Customer] = relationship()
    user: Mapped[User] = relationship()


class Opportunity(Base):
    __tablename__ = "opportunities"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(220))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    stage: Mapped[OpportunityStage] = mapped_column(Enum(OpportunityStage), default=OpportunityStage.new, index=True)
    next_action: Mapped[str | None] = mapped_column(String(255))
    next_action_date: Mapped[date | None] = mapped_column(Date, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    customer: Mapped[Customer] = relationship()
    owner: Mapped[User] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity_type: Mapped[str] = mapped_column(String(80), index=True)
    entity_id: Mapped[int | None] = mapped_column(index=True)
    description: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    user: Mapped[User] = relationship()
