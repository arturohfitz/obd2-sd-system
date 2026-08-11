import os
from uuid import uuid4
os.environ["DATABASE_URL"] = "sqlite:///./test_obd2sd.db"
os.environ["SECRET_KEY"] = "test-secret-not-for-production"
os.environ["UPLOAD_DIR"] = "./test_uploads"
from fastapi.testclient import TestClient
from app.main import app


def test_complete_commercial_flow():
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "ok"
        login = client.post("/api/auth/login", json={"email": "admin@obd2solucionesdiesel.com", "password": "CambiarEstaClave123!"})
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        unique_phone = "52" + str(uuid4().int)[:10]
        customer = client.post("/api/customers", headers=headers, json={"name":"Transportes Prueba","company":"Transportes Prueba","phone":unique_phone,"status":"active"})
        assert customer.status_code == 201
        sales_email = f"ventas-{uuid4().hex[:8]}@example.com"
        sales_user = client.post("/api/users", headers=headers, json={"name":"Vendedor Prueba","email":sales_email,"password":"VentaSegura123!","role":"sales"})
        assert sales_user.status_code == 201
        sales_login = client.post("/api/auth/login", json={"email":sales_email,"password":"VentaSegura123!"})
        sales_headers = {"Authorization": f"Bearer {sales_login.json()['access_token']}"}
        forbidden_product = client.post("/api/products", headers=sales_headers, json={"name":f"Restringido {uuid4()}","category":"Producto","price":100})
        assert forbidden_product.status_code == 403
        owner = client.put(f"/api/customers/{customer.json()['id']}/owner", headers=headers, json={"user_id":sales_user.json()["id"]})
        assert owner.status_code == 200
        opportunity = client.post("/api/opportunities", headers=sales_headers, json={"customer_id":customer.json()["id"],"owner_id":sales_user.json()["id"],"title":"Renovación de equipo","amount":25000,"stage":"quoted","next_action":"Revisar propuesta","next_action_date":"2026-08-20"})
        assert opportunity.status_code == 201
        agenda = client.get("/api/agenda", headers=sales_headers)
        assert agenda.status_code == 200 and any(item["id"] == opportunity.json()["id"] for item in agenda.json())
        sale = client.post("/api/sales", headers=headers, json={"customer_id":customer.json()["id"],"concept":"Diagnóstico de unidad","amount":18000,"status":"won","sale_date":"2026-08-11"})
        assert sale.status_code == 201 and sale.json()["balance"] == "18000.00"
        payment = client.post("/api/payments", headers=headers, json={"sale_id":sale.json()["id"],"amount":6000,"paid_at":"2026-08-11","method":"Transferencia"})
        assert payment.status_code == 201
        promise = client.post("/api/promises", headers=headers, json={"sale_id":sale.json()["id"],"amount":6000,"due_date":"2026-08-15","status":"pending"})
        assert promise.status_code == 201
        activity = client.post(
            f"/api/customers/{customer.json()['id']}/activities",
            headers=headers,
            json={"activity_type": "call", "description": "Cliente confirmó seguimiento", "follow_up_date": "2026-08-20"},
        )
        assert activity.status_code == 201
        upload = client.post(
            f"/api/customers/{customer.json()['id']}/files",
            headers=headers,
            data={"description": "Comprobante demo"},
            files={"file": ("comprobante.pdf", b"%PDF-1.4 demo", "application/pdf")},
        )
        assert upload.status_code == 201
        download = client.get(f"/api/customer-files/{upload.json()['id']}/download", headers=headers)
        assert download.status_code == 200 and download.content.startswith(b"%PDF")
        detail = client.get(f"/api/customers/{customer.json()['id']}", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["activities"] and detail.json()["files"]
        cancellable = client.post("/api/sales", headers=headers, json={"customer_id":customer.json()["id"],"concept":"Venta cancelable","amount":1000,"status":"won","sale_date":"2026-08-11"})
        cancelled = client.patch(f"/api/sales/{cancellable.json()['id']}/cancel", headers=headers)
        assert cancelled.status_code == 200 and cancelled.json()["status"] == "cancelled"
        refused = client.patch(f"/api/sales/{sale.json()['id']}/cancel", headers=headers)
        assert refused.status_code == 400
        summary = client.get("/api/reports/summary?date_from=2026-08-01&date_to=2026-08-31", headers=headers)
        assert summary.status_code == 200 and float(summary.json()["sales"]) > 0
        receivables = client.get("/api/reports/receivables", headers=headers)
        assert receivables.status_code == 200
        export = client.get("/api/reports/export/sales?date_from=2026-08-01&date_to=2026-08-31", headers=headers)
        assert export.status_code == 200 and "Cliente" in export.text
        audit = client.get("/api/audit", headers=headers)
        assert audit.status_code == 200 and audit.json()
        forbidden_audit = client.get("/api/audit", headers=sales_headers)
        assert forbidden_audit.status_code == 403
        sales = client.get("/api/sales", headers=headers).json()
        original = next(item for item in sales if item["id"] == sale.json()["id"])
        assert original["balance"] == "12000.00"
