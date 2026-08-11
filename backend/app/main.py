from contextlib import asynccontextmanager
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload
from .auth import create_token, current_user, hash_password, require_roles, verify_password
from .config import get_settings
from .database import Base, SessionLocal, engine, get_db
from .models import Customer, CustomerActivity, CustomerFile, CustomerOwner, CustomerStatus, Opportunity, OpportunityStage, Payment, PaymentPromise, Product, PromiseStatus, Sale, SaleStatus, User
from .schemas import ActivityIn, ActivityOut, AdminPasswordReset, CustomerDetail, CustomerFileOut, CustomerIn, CustomerOut, CustomerOwnerOut, DashboardOut, LoginIn, LoginOut, OpportunityIn, OpportunityOut, OwnerAssignment, PasswordChange, PaymentIn, PaymentOut, ProductIn, ProductOut, PromiseIn, PromiseOut, SaleIn, SaleOut, UserCreate, UserOut, UserUpdate


settings = get_settings()


def money(value) -> Decimal:
    return Decimal(value or 0).quantize(Decimal("0.01"))


def log_activity(db: Session, customer_id: int, user_id: int, activity_type: str, description: str, follow_up_date=None):
    db.add(CustomerActivity(customer_id=customer_id, user_id=user_id, activity_type=activity_type, description=description, follow_up_date=follow_up_date))


def activity_out(item: CustomerActivity) -> ActivityOut:
    return ActivityOut.model_validate({**item.__dict__, "user_name": item.user.name})


def file_out(item: CustomerFile) -> CustomerFileOut:
    return CustomerFileOut.model_validate({**item.__dict__, "user_name": item.user.name})


def customer_balance(customer: Customer) -> Decimal:
    balance = sum(
        (
            money(sale.amount) - sum((money(payment.amount) for payment in sale.payments), Decimal("0"))
            for sale in customer.sales
            if sale.status == SaleStatus.won
        ),
        Decimal("0"),
    )
    return max(balance, Decimal("0"))


def opportunity_out(item: Opportunity) -> OpportunityOut:
    return OpportunityOut.model_validate({
        **item.__dict__,
        "customer_name": item.customer.name,
        "owner_name": item.owner.name,
    })


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


@app.patch("/api/auth/password")
def change_password(data: PasswordChange, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(400, "La contraseña actual no es correcta")
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "Contraseña actualizada"}


@app.get("/api/users", response_model=list[UserOut])
def users(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return db.scalars(select(User).order_by(User.active.desc(), User.name)).all()


@app.post("/api/users", response_model=UserOut, status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    roles = {"admin", "sales", "collections", "viewer"}
    if data.role not in roles:
        raise HTTPException(400, "Rol no válido")
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Ya existe un usuario con ese correo")
    item = User(name=data.name, email=email, password_hash=hash_password(data.password), role=data.role)
    db.add(item); db.commit(); db.refresh(item)
    return item


@app.patch("/api/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))):
    item = db.get(User, user_id)
    if not item:
        raise HTTPException(404, "Usuario no encontrado")
    if item.id == admin.id and not data.active:
        raise HTTPException(400, "No puedes desactivar tu propia cuenta")
    if data.role not in {"admin", "sales", "collections", "viewer"}:
        raise HTTPException(400, "Rol no válido")
    item.name, item.role, item.active = data.name, data.role, data.active
    db.commit(); db.refresh(item)
    return item


@app.patch("/api/users/{user_id}/password")
def reset_user_password(user_id: int, data: AdminPasswordReset, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    item = db.get(User, user_id)
    if not item:
        raise HTTPException(404, "Usuario no encontrado")
    item.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "Contraseña restablecida"}


@app.get("/api/customers", response_model=list[CustomerOut])
def customers(search: str = Query("", max_length=100), db: Session = Depends(get_db), _: User = Depends(current_user)):
    query = select(Customer).options(selectinload(Customer.sales).selectinload(Sale.payments)).order_by(Customer.created_at.desc())
    if search:
        term = f"%{search}%"
        query = query.where(or_(Customer.name.ilike(term), Customer.company.ilike(term), Customer.phone.ilike(term)))
    result = []
    for customer in db.scalars(query).unique():
        result.append(CustomerOut.model_validate({**customer.__dict__, "balance": customer_balance(customer)}))
    return result


@app.get("/api/customers/{customer_id}", response_model=CustomerDetail)
def customer_detail(customer_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    query = (
        select(Customer)
        .where(Customer.id == customer_id)
        .options(
            selectinload(Customer.sales).selectinload(Sale.payments),
            selectinload(Customer.activities).selectinload(CustomerActivity.user),
            selectinload(Customer.files).selectinload(CustomerFile.user),
        )
    )
    customer = db.scalar(query)
    if not customer:
        raise HTTPException(404, "Cliente no encontrado")
    ordered_sales = sorted(customer.sales, key=lambda sale: (sale.sale_date, sale.id), reverse=True)
    ordered_activities = sorted(customer.activities, key=lambda item: item.created_at, reverse=True)
    ordered_files = sorted(customer.files, key=lambda item: item.created_at, reverse=True)
    return CustomerDetail.model_validate({
        **customer.__dict__,
        "balance": customer_balance(customer),
        "sales": [sale_out(sale) for sale in ordered_sales],
        "activities": [activity_out(item) for item in ordered_activities],
        "files": [file_out(item) for item in ordered_files],
    })


@app.post("/api/customers", response_model=CustomerOut, status_code=201)
def create_customer(data: CustomerIn, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "sales"))):
    phone = "".join(char for char in data.phone if char.isdigit())
    if db.scalar(select(Customer).where(Customer.phone == phone)):
        raise HTTPException(status_code=409, detail="Ya existe un cliente con ese teléfono")
    item = Customer(**data.model_dump(exclude={"phone"}), phone=phone)
    db.add(item); db.flush()
    log_activity(db, item.id, user.id, "created", "Ficha del cliente creada.")
    db.commit(); db.refresh(item)
    return CustomerOut.model_validate({**item.__dict__, "balance": 0})


@app.patch("/api/customers/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: int, data: CustomerIn, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "sales"))):
    item = db.scalar(select(Customer).where(Customer.id == customer_id).options(selectinload(Customer.sales).selectinload(Sale.payments)))
    if not item: raise HTTPException(404, "Cliente no encontrado")
    values = data.model_dump(); values["phone"] = "".join(c for c in data.phone if c.isdigit())
    for key, value in values.items(): setattr(item, key, value)
    log_activity(db, item.id, user.id, "updated", "Información general del cliente actualizada.", data.next_follow_up)
    db.commit(); db.refresh(item)
    return CustomerOut.model_validate({**item.__dict__, "balance": customer_balance(item)})


@app.post("/api/customers/{customer_id}/activities", response_model=ActivityOut, status_code=201)
def create_activity(customer_id: int, data: ActivityIn, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "sales", "collections"))):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, "Cliente no encontrado")
    item = CustomerActivity(customer_id=customer_id, user_id=user.id, **data.model_dump())
    if data.follow_up_date:
        customer.next_follow_up = data.follow_up_date
    db.add(item); db.commit()
    item = db.scalar(select(CustomerActivity).where(CustomerActivity.id == item.id).options(selectinload(CustomerActivity.user)))
    return activity_out(item)


@app.post("/api/customers/{customer_id}/files", response_model=CustomerFileOut, status_code=201)
async def upload_customer_file(
    customer_id: int,
    file: UploadFile = File(...),
    description: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "sales", "collections")),
):
    if not db.get(Customer, customer_id):
        raise HTTPException(404, "Cliente no encontrado")
    allowed_types = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
    content_type = file.content_type or "application/octet-stream"
    if content_type not in allowed_types:
        raise HTTPException(400, "Solo se permiten archivos PDF, JPG, PNG o WEBP")
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "El archivo supera el límite de 10 MB")
    original_name = Path(file.filename or "documento").name[:255]
    suffix = Path(original_name).suffix.lower()
    stored_name = f"{uuid4().hex}{suffix}"
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / stored_name).write_bytes(content)
    item = CustomerFile(
        customer_id=customer_id,
        user_id=user.id,
        original_name=original_name,
        stored_name=stored_name,
        content_type=content_type,
        size=len(content),
        description=(description or "").strip()[:255] or None,
    )
    db.add(item)
    log_activity(db, customer_id, user.id, "file", f"Documento adjuntado: {original_name}")
    db.commit()
    item = db.scalar(select(CustomerFile).where(CustomerFile.id == item.id).options(selectinload(CustomerFile.user)))
    return file_out(item)


@app.get("/api/customer-files/{file_id}/download")
def download_customer_file(file_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    item = db.get(CustomerFile, file_id)
    if not item:
        raise HTTPException(404, "Documento no encontrado")
    path = Path(settings.upload_dir) / item.stored_name
    if not path.is_file():
        raise HTTPException(404, "El archivo físico no está disponible")
    return FileResponse(path, media_type=item.content_type, filename=item.original_name)


@app.get("/api/products", response_model=list[ProductOut])
def products(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return db.scalars(select(Product).order_by(Product.name)).all()


@app.post("/api/products", response_model=ProductOut, status_code=201)
def create_product(data: ProductIn, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    item = Product(**data.model_dump()); db.add(item); db.commit(); db.refresh(item); return item


@app.get("/api/sales", response_model=list[SaleOut])
def sales(db: Session = Depends(get_db), _: User = Depends(current_user)):
    query = select(Sale).options(selectinload(Sale.customer), selectinload(Sale.payments)).order_by(Sale.sale_date.desc(), Sale.id.desc())
    return [sale_out(item) for item in db.scalars(query)]


@app.post("/api/sales", response_model=SaleOut, status_code=201)
def create_sale(data: SaleIn, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "sales"))):
    if not db.get(Customer, data.customer_id): raise HTTPException(404, "Cliente no encontrado")
    item = Sale(**data.model_dump()); db.add(item); db.flush()
    log_activity(db, item.customer_id, user.id, "sale", f"Venta registrada: {item.concept} por {money(item.amount)} MXN.")
    db.commit()
    item = db.scalar(select(Sale).where(Sale.id == item.id).options(selectinload(Sale.customer), selectinload(Sale.payments)))
    return sale_out(item)


@app.post("/api/payments", response_model=PaymentOut, status_code=201)
def create_payment(data: PaymentIn, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "collections"))):
    sale = db.scalar(select(Sale).where(Sale.id == data.sale_id).options(selectinload(Sale.payments)))
    if not sale: raise HTTPException(404, "Venta no encontrada")
    balance = money(sale.amount) - sum((money(p.amount) for p in sale.payments), Decimal("0"))
    if money(data.amount) > balance: raise HTTPException(400, f"El abono supera el saldo de {balance}")
    item = Payment(**data.model_dump()); db.add(item)
    log_activity(db, sale.customer_id, user.id, "payment", f"Pago registrado por {money(item.amount)} MXN para {sale.concept}.")
    db.commit(); db.refresh(item)
    return item


@app.patch("/api/sales/{sale_id}/cancel", response_model=SaleOut)
def cancel_sale(sale_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    sale = db.scalar(select(Sale).where(Sale.id == sale_id).options(selectinload(Sale.customer), selectinload(Sale.payments)))
    if not sale:
        raise HTTPException(404, "Venta no encontrada")
    if sale.payments:
        raise HTTPException(400, "No se puede cancelar una venta que ya tiene pagos registrados")
    sale.status = SaleStatus.cancelled
    log_activity(db, sale.customer_id, user.id, "cancelled", f"Venta cancelada: {sale.concept}.")
    db.commit()
    return sale_out(sale)


@app.get("/api/promises", response_model=list[PromiseOut])
def promises(db: Session = Depends(get_db), _: User = Depends(current_user)):
    query = select(PaymentPromise).options(selectinload(PaymentPromise.sale).selectinload(Sale.customer)).order_by(PaymentPromise.due_date)
    return [promise_out(item) for item in db.scalars(query)]


@app.post("/api/promises", response_model=PromiseOut, status_code=201)
def create_promise(data: PromiseIn, db: Session = Depends(get_db), _: User = Depends(require_roles("admin", "collections"))):
    sale = db.scalar(select(Sale).where(Sale.id == data.sale_id).options(selectinload(Sale.customer)))
    if not sale: raise HTTPException(404, "Venta no encontrada")
    item = PaymentPromise(**data.model_dump()); db.add(item); db.commit(); db.refresh(item); item.sale = sale
    return promise_out(item)


@app.patch("/api/promises/{promise_id}/paid", response_model=PromiseOut)
def mark_promise_paid(promise_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("admin", "collections"))):
    item = db.scalar(select(PaymentPromise).where(PaymentPromise.id == promise_id).options(selectinload(PaymentPromise.sale).selectinload(Sale.customer)))
    if not item: raise HTTPException(404, "Promesa no encontrada")
    item.status = PromiseStatus.paid; db.commit(); return promise_out(item)


@app.get("/api/customers/{customer_id}/owner", response_model=CustomerOwnerOut | None)
def customer_owner(customer_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    item = db.scalar(select(CustomerOwner).where(CustomerOwner.customer_id == customer_id).options(selectinload(CustomerOwner.user)))
    if not item:
        return None
    return CustomerOwnerOut(customer_id=item.customer_id, user_id=item.user_id, user_name=item.user.name)


@app.put("/api/customers/{customer_id}/owner", response_model=CustomerOwnerOut)
def assign_customer_owner(customer_id: int, data: OwnerAssignment, db: Session = Depends(get_db), actor: User = Depends(require_roles("admin", "sales"))):
    if not db.get(Customer, customer_id):
        raise HTTPException(404, "Cliente no encontrado")
    owner = db.get(User, data.user_id)
    if not owner or not owner.active:
        raise HTTPException(400, "El responsable no está disponible")
    item = db.get(CustomerOwner, customer_id)
    if item:
        item.user_id = data.user_id
    else:
        item = CustomerOwner(customer_id=customer_id, user_id=data.user_id)
        db.add(item)
    log_activity(db, customer_id, actor.id, "assignment", f"Cliente asignado a {owner.name}.")
    db.commit()
    return CustomerOwnerOut(customer_id=customer_id, user_id=owner.id, user_name=owner.name)


@app.get("/api/opportunities", response_model=list[OpportunityOut])
def opportunities(mine: bool = False, db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = select(Opportunity).options(selectinload(Opportunity.customer), selectinload(Opportunity.owner)).order_by(Opportunity.updated_at.desc())
    if mine:
        query = query.where(Opportunity.owner_id == user.id)
    return [opportunity_out(item) for item in db.scalars(query)]


@app.post("/api/opportunities", response_model=OpportunityOut, status_code=201)
def create_opportunity(data: OpportunityIn, db: Session = Depends(get_db), actor: User = Depends(require_roles("admin", "sales"))):
    customer = db.get(Customer, data.customer_id)
    owner = db.get(User, data.owner_id)
    if not customer:
        raise HTTPException(404, "Cliente no encontrado")
    if not owner or not owner.active:
        raise HTTPException(400, "Responsable no disponible")
    item = Opportunity(**data.model_dump())
    db.add(item); db.flush()
    log_activity(db, customer.id, actor.id, "opportunity", f"Oportunidad creada: {item.title} por {money(item.amount)} MXN.", item.next_action_date)
    db.commit()
    item = db.scalar(select(Opportunity).where(Opportunity.id == item.id).options(selectinload(Opportunity.customer), selectinload(Opportunity.owner)))
    return opportunity_out(item)


@app.patch("/api/opportunities/{opportunity_id}", response_model=OpportunityOut)
def update_opportunity(opportunity_id: int, data: OpportunityIn, db: Session = Depends(get_db), actor: User = Depends(require_roles("admin", "sales"))):
    item = db.get(Opportunity, opportunity_id)
    if not item:
        raise HTTPException(404, "Oportunidad no encontrada")
    owner = db.get(User, data.owner_id)
    if not owner or not owner.active:
        raise HTTPException(400, "Responsable no disponible")
    old_stage = item.stage
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    if old_stage != item.stage:
        log_activity(db, item.customer_id, actor.id, "opportunity", f"Oportunidad movida de {old_stage.value} a {item.stage.value}.", item.next_action_date)
    db.commit()
    item = db.scalar(select(Opportunity).where(Opportunity.id == item.id).options(selectinload(Opportunity.customer), selectinload(Opportunity.owner)))
    return opportunity_out(item)


@app.get("/api/agenda", response_model=list[OpportunityOut])
def agenda(db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = (
        select(Opportunity)
        .where(
            Opportunity.owner_id == user.id,
            Opportunity.next_action_date.is_not(None),
            Opportunity.stage.not_in([OpportunityStage.won, OpportunityStage.lost]),
        )
        .options(selectinload(Opportunity.customer), selectinload(Opportunity.owner))
        .order_by(Opportunity.next_action_date)
    )
    return [opportunity_out(item) for item in db.scalars(query)]


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
