"""Carga un escenario comercial demostrativo sin duplicar registros."""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import (
    Customer,
    CustomerStatus,
    Payment,
    PaymentPromise,
    Product,
    PromiseStatus,
    Sale,
    SaleStatus,
)


DEMO_MARKER = "[DATOS DEMO OBD2 SD]"


PRODUCTS = [
    ("Diagnóstico electrónico diésel", "Servicio", "2800.00"),
    ("Programación de módulo ECM", "Servicio", "12500.00"),
    ("Eliminación DPF / EGR", "Servicio", "9500.00"),
    ("Escáner profesional multimarca", "Producto", "48500.00"),
    ("Licencia de diagnóstico anual", "Licencia", "16800.00"),
    ("Reparación de módulo de control", "Servicio", "18500.00"),
]


CUSTOMERS = [
    ("Carlos Ramírez", "Transportes del Centro", "5213300000001", CustomerStatus.active),
    ("Mariana Torres", "Logística del Bajío", "5213300000002", CustomerStatus.active),
    ("José Hernández", "Autotransportes Hernández", "5213300000003", CustomerStatus.active),
    ("Daniela Mendoza", "Diesel Express Norte", "5213300000004", CustomerStatus.active),
    ("Roberto Sánchez", "Fletes San Pedro", "5213300000005", CustomerStatus.active),
    ("Ana López", "Taller López Diésel", "5213300000006", CustomerStatus.active),
    ("Miguel Castillo", "Carga Segura MX", "5213300000007", CustomerStatus.prospect),
    ("Laura Jiménez", "Servicios Técnicos Jalisco", "5213300000008", CustomerStatus.prospect),
]


SALES = [
    # cliente, producto, monto, días desde venta, pago, vencimiento promesa, monto promesa
    (0, 1, "18000", -35, "6000", -15, "6000"),
    (1, 3, "48500", -28, "20000", -7, "15000"),
    (2, 2, "12500", -18, "3000", -3, "5000"),
    (3, 5, "22000", -12, "7000", -1, "7500"),
    (4, 0, "8500", -7, "2500", 0, "3000"),
    (5, 4, "16800", -5, "6800", 3, "5000"),
    (0, 0, "4200", -3, "0", 7, "4200"),
    (2, 5, "18500", -2, "10000", 15, "8500"),
]


def get_or_create_product(db, name: str, category: str, price: str) -> Product:
    product = db.scalar(select(Product).where(Product.name == name))
    if not product:
        product = Product(name=name, category=category, price=Decimal(price), active=True)
        db.add(product)
        db.flush()
    return product


def get_or_create_customer(db, name: str, company: str, phone: str, status: CustomerStatus) -> Customer:
    customer = db.scalar(select(Customer).where(Customer.phone == phone))
    if not customer:
        customer = Customer(
            name=name,
            company=company,
            phone=phone,
            email=f"demo{phone[-2:]}@obd2solucionesdiesel.com",
            status=status,
            notes=f"{DEMO_MARKER} Registro para pruebas del portal.",
            next_follow_up=date.today() + timedelta(days=2) if status == CustomerStatus.prospect else None,
        )
        db.add(customer)
        db.flush()
    return customer


def seed_demo() -> dict[str, int]:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        products = [get_or_create_product(db, *item) for item in PRODUCTS]
        customers = [get_or_create_customer(db, *item) for item in CUSTOMERS]

        existing_demo_sale = db.scalar(select(Sale).where(Sale.notes.like(f"%{DEMO_MARKER}%")))
        created_sales = 0
        if not existing_demo_sale:
            for index, row in enumerate(SALES, start=1):
                customer_index, product_index, amount, sold_delta, paid, due_delta, promised = row
                product = products[product_index]
                sale = Sale(
                    customer_id=customers[customer_index].id,
                    product_id=product.id,
                    concept=product.name,
                    vehicle=f"Unidad demo {index:02d}",
                    amount=Decimal(amount),
                    status=SaleStatus.won,
                    sale_date=date.today() + timedelta(days=sold_delta),
                    notes=f"{DEMO_MARKER} Operación de prueba {index:02d}.",
                )
                db.add(sale)
                db.flush()
                if Decimal(paid) > 0:
                    db.add(
                        Payment(
                            sale_id=sale.id,
                            amount=Decimal(paid),
                            paid_at=sale.sale_date + timedelta(days=2),
                            method="Transferencia",
                            reference=f"DEMO-{index:04d}",
                            notes=DEMO_MARKER,
                        )
                    )
                db.add(
                    PaymentPromise(
                        sale_id=sale.id,
                        amount=Decimal(promised),
                        due_date=date.today() + timedelta(days=due_delta),
                        status=PromiseStatus.pending,
                        notes=f"{DEMO_MARKER} Compromiso de prueba.",
                    )
                )
                created_sales += 1
        db.commit()
        return {
            "products": len(products),
            "customers": len(customers),
            "sales_created": created_sales,
        }


if __name__ == "__main__":
    result = seed_demo()
    print(
        "Datos demo disponibles: "
        f"{result['customers']} clientes, {result['products']} conceptos, "
        f"{result['sales_created']} ventas nuevas."
    )
