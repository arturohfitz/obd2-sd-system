import os
from uuid import uuid4
os.environ["DATABASE_URL"] = "sqlite:///./test_obd2sd.db"
os.environ["SECRET_KEY"] = "test-secret-not-for-production"
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
        sales = client.get("/api/sales", headers=headers).json()
        original = next(item for item in sales if item["id"] == sale.json()["id"])
        assert original["balance"] == "12000.00"
