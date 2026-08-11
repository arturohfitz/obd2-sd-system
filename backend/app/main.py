from contextlib import asynccontextmanager
from datetime import date, timedelta
from decimal import Decimal
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload
from .auth import create_token, current_user, hash_password, verify_password
from .config import get_settings
from .database import Base, SessionLocal, engine, get_db
from .models import Customer, CustomerStatus, Payment, PaymentPromise, Product, PromiseStatus, Sale, SaleStatus, User
from .schemas import CustomerIn, CustomerOut, DashboardOut, LoginIn, LoginOut, PaymentIn, PaymentOut, ProductIn, ProductOut, PromiseIn, PromiseOut, SaleIn, SaleOut, UserOut


settings = get_settings()


def money(value) -> Decimal:
    return Decimal(value or 0).quantize(Decimal("0.01"))


def sale_out(sale: Sale) -> SaleOut:
    paid = sum((money(p.amount) for p in sale.payments), Decimal("0"))
    return SaleOut.model_validate({
        "id": sale.id, "customer_id": sale.customer_id, "product_id": sale.product_id,
        "concept": sale.concept, "vehicle": sale.vehicle, "amount": sale.amount,
        "status": sale.status, "sale_date": sale.sale_date, "notes": sale.notes,
        "customer_name": sale.customer.name, "paid": paid,
        "balance": max(money(sale.amount) - paid, Decimal("0")),
    })


def promise_out(item: PaymentPromise) -> PromiseOut:
    overdue = max((date.today() - item.due_date).days, 0) if item.status == PromiseStatus.pending else 0
    return PromiseOut.model_validate({
        "id": item.id, "sale_id": item.sale_id, "amount": item.amount,
        "due_date": item.due_date, "status": item.status, "notes": item.notes,
        "customer_name": item.sale.customer.name, "concept": item.sale.concept,
        "days_overdue": overdue,
    })


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        email = settings.initial_admin_email.lower()
        if not db.scalar(select(User).where(User.email == email)):
            db.add(User(name="Administrador", email=email, password_hash=hash_password(settings.initial_admin_password), role="admin"))
            db.commit()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}


@app.post("/api/auth/login", response_model=LoginOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not verify_password(data.password, user.password_hash) or not user.active:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    return LoginOut(access_token=create_token(user), user=UserOut.model_validate(user))


@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@app.get("/api/customers", response_model=list[CustomerOut])
def customers(search: str = Query("", max_length=100), db: Session = Depends(get_db), _: User = Depends(current_user)):
    query = select(Customer).options(selectinload(Customer.sales).selectinload(Sale.payments)).order_by(Customer.created_at.desc())
    if search:
        term = f"%{search}%"
        query = query.where(or_(Customer.name.ilike(term), Customer.company.ilike(term), Customer.phone.ilike(term)))
    result = []
    for customer in db.scalars(query).unique():
        balance = sum((money(s.amount) - sum((money(p.amount) for p in s.payments), Decimal("0")) for s in customer.sales if s.status == SaleStatus.won), Decimal("0"))
        result.append(CustomerOut.model_validate({**customer.__dict__, "balance": max(balance, Decimal("0"))}))
    return result


@app.post("/api/customers", response_model=CustomerOut, status_code=201)
def create_customer(data: CustomerIn, db: Session = Depends(get_db), _: User = Depends(current_user)):
    phone = "".join(char for char in data.phone if char.isdigit())
    if db.scalar(select(Customer).where(Customer.phone == phone)):
        raise HTTPException(status_code=409, detail="Ya existe un cliente con ese teléfono")
    item = Customer(**data.model_dump(exclude={"phone"}), phone=phone)
    db.add(item); db.commit(); db.refresh(item)
    return CustomerOut.model_validate({**item.__dict__, "balance": 0})


@app.patch("/api/customers/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: int, data: CustomerIn, db: Session = Depends(get_db), _: User = Depends(current_user)):
    item = db.get(Customer, customer_id)
    if not item: raise HTTPException(404, "Cliente no encontrado")
    values = data.model_dump(); values["phone"] = "".join(c for c in data.phone if c.isdigit())
    for key, value in values.items(): setattr(item, key, value)
    db.commit(); db.refresh(item)
    return CustomerOut.model_validate({**item.__dict__, "balance": 0})


@app.get("/api/products", response_model=list[ProductOut])
def products(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return db.scalars(select(Product).order_by(Product.name)).all()


@app.post("/api/products", response_model=ProductOut, status_code=201)
def create_product(data: ProductIn, db: Session = Depends(get_db), _: User = Depends(current_user)):
    item = Product(**data.model_dump()); db.add(item); db.commit(); db.refresh(item); return item


@app.get("/api/sales", response_model=list[SaleOut])
def sales(db: Session = Depends(get_db), _: User = Depends(current_user)):
    query = select(Sale).options(selectinload(Sale.customer), selectinload(Sale.payments)).order_by(Sale.sale_date.desc(), Sale.id.desc())
    return [sale_out(item) for item in db.scalars(query)]


@app.post("/api/sales", response_model=SaleOut, status_code=201)
def create_sale(data: SaleIn, db: Session = Depends(get_db), _: User = Depends(current_user)):
    if not db.get(Customer, data.customer_id): raise HTTPException(404, "Cliente no encontrado")
    item = Sale(**data.model_dump()); db.add(item); db.commit()
    item = db.scalar(select(Sale).where(Sale.id == item.id).options(selectinload(Sale.customer), selectinload(Sale.payments)))
    return sale_out(item)


@app.post("/api/payments", response_model=PaymentOut, status_code=201)
def create_payment(data: PaymentIn, db: Session = Depends(get_db), _: User = Depends(current_user)):
    sale = db.scalar(select(Sale).where(Sale.id == data.sale_id).options(selectinload(Sale.payments)))
    if not sale: raise HTTPException(404, "Venta no encontrada")
    balance = money(sale.amount) - sum((money(p.amount) for p in sale.payments), Decimal("0"))
    if money(data.amount) > balance: raise HTTPException(400, f"El abono supera el saldo de {balance}")
    item = Payment(**data.model_dump()); db.add(item); db.commit(); db.refresh(item)
    return item


@app.get("/api/promises", response_model=list[PromiseOut])
def promises(db: Session = Depends(get_db), _: User = Depends(current_user)):
    query = select(PaymentPromise).options(selectinload(PaymentPromise.sale).selectinload(Sale.customer)).order_by(PaymentPromise.due_date)
    return [promise_out(item) for item in db.scalars(query)]


@app.post("/api/promises", response_model=PromiseOut, status_code=201)
def create_promise(data: PromiseIn, db: Session = Depends(get_db), _: User = Depends(current_user)):
    sale = db.scalar(select(Sale).where(Sale.id == data.sale_id).options(selectinload(Sale.customer)))
    if not sale: raise HTTPException(404, "Venta no encontrada")
    item = PaymentPromise(**data.model_dump()); db.add(item); db.commit(); db.refresh(item); item.sale = sale
    return promise_out(item)


@app.patch("/api/promises/{promise_id}/paid", response_model=PromiseOut)
def mark_promise_paid(promise_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    item = db.scalar(select(PaymentPromise).where(PaymentPromise.id == promise_id).options(selectinload(PaymentPromise.sale).selectinload(Sale.customer)))
    if not item: raise HTTPException(404, "Promesa no encontrada")
    item.status = PromiseStatus.paid; db.commit(); return promise_out(item)


@app.get("/api/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db), _: User = Depends(current_user)):
    total_sales = money(db.scalar(select(func.sum(Sale.amount)).where(Sale.status == SaleStatus.won)))
    total_collected = money(db.scalar(select(func.sum(Payment.amount))))
    today = date.today(); week = today + timedelta(days=7)
    overdue = money(db.scalar(select(func.sum(PaymentPromise.amount)).where(PaymentPromise.status == PromiseStatus.pending, PaymentPromise.due_date < today)))
    due_today = money(db.scalar(select(func.sum(PaymentPromise.amount)).where(PaymentPromise.status == PromiseStatus.pending, PaymentPromise.due_date == today)))
    due_next = money(db.scalar(select(func.sum(PaymentPromise.amount)).where(PaymentPromise.status == PromiseStatus.pending, PaymentPromise.due_date > today, PaymentPromise.due_date <= week)))
    overdue_customers = db.scalar(select(func.count(func.distinct(Sale.customer_id))).join(PaymentPromise).where(PaymentPromise.status == PromiseStatus.pending, PaymentPromise.due_date < today)) or 0
    active_customers = db.scalar(select(func.count(Customer.id)).where(Customer.status == CustomerStatus.active)) or 0
    return DashboardOut(total_sales=total_sales, total_collected=total_collected, total_receivable=max(total_sales-total_collected, Decimal("0")), overdue=overdue, due_today=due_today, due_next_7_days=due_next, active_customers=active_customers, overdue_customers=overdue_customers)
