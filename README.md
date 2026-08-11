# OBD2 SD System

Portal web responsive para el control comercial, servicios, pagos, fechas promesa y cobranza de OBD2 Soluciones Diésel.

## Funciones disponibles

- Panel ejecutivo de ventas, cobros, saldos y cartera vencida.
- Clientes y prospectos identificados por su número de WhatsApp.
- Catálogo básico de productos y servicios.
- Registro de ventas, trabajos y unidades.
- Abonos con validación contra el saldo pendiente.
- Fechas promesa, cumplimiento y días de mora.
- Diseño adaptable a computadora, tablet y celular.
- API protegida con autenticación y perfiles preparados para ampliación.

## Desarrollo local

### API

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload
```

La API estará en `http://localhost:8000` y su documentación en `http://localhost:8000/docs`.

### Portal

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

Abrir `http://localhost:5173`. En desarrollo, las credenciales iniciales provienen de `.env.example` y deben cambiarse antes de usar datos reales.

### Datos de demostración

Con la API detenida o desde otra terminal ubicada en `backend`, ejecutar:

```bash
PYTHONPATH=. ../.venv/bin/python -m scripts.seed_demo
```

El comando agrega clientes, prospectos, catálogo, ventas, pagos y promesas con fechas relativas al día de ejecución. Puede repetirse sin duplicar el escenario demo.

## Producción con Docker

Crear `.env` con valores únicos y seguros:

```env
POSTGRES_PASSWORD=una-clave-larga-y-unica
SECRET_KEY=una-clave-aleatoria-de-al-menos-64-caracteres
INITIAL_ADMIN_EMAIL=admin@obd2solucionesdiesel.com
INITIAL_ADMIN_PASSWORD=otra-clave-larga-y-unica
CORS_ORIGINS=https://portal.obd2solucionesdiesel.com
WEB_PORT=8080
```

Después ejecutar:

```bash
docker compose up -d --build
curl http://localhost:8080/health
```

El servicio se expone en el puerto `8080` para conectarlo al proxy HTTPS que ya administre la VPS. No ocupa directamente los puertos `80/443`.

## Subdominio propuesto

Crear un registro DNS `A` para `portal.obd2solucionesdiesel.com` apuntando a la IP pública de la VPS. En el proxy de la VPS se configura HTTPS y se dirige el subdominio a `http://127.0.0.1:8080`.

No se deben publicar PostgreSQL ni el puerto interno de la API. Antes de desplegar es necesario revisar los contenedores, proxy y puertos que ya estén operando en la VPS.

## Próximas etapas

1. Edición detallada de clientes, ventas y catálogo; archivos y comprobantes.
2. Embudo comercial, actividades y responsables.
3. Integración controlada con WhatsApp Business Platform.
4. Plantillas y reglas automáticas de cobranza con aprobación manual inicial.
5. Reportes exportables, auditoría, respaldos y administración de usuarios.
