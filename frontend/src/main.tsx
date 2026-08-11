import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BarChart3,
  BriefcaseBusiness,
  CalendarClock,
  ChevronRight,
  ClipboardList,
  LogOut,
  Menu,
  Package,
  Plus,
  Search,
  Users,
  WalletCards,
  X,
} from "lucide-react";
import { api } from "./api";
import type { Customer, Dashboard, Product, PromiseItem, Sale } from "./types";
import "./styles.css";

const money = (n: number) =>
  new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" }).format(
    n || 0,
  );
const today = () => new Date().toISOString().slice(0, 10);
type Page = "dashboard" | "customers" | "sales" | "collections" | "products";

function Login({ done }: { done: () => void }) {
  const [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const r = await api<{ access_token: string }>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem("obd2_token", r.access_token);
      done();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login">
      <section className="login-card">
        <div className="brand-mark">SD</div>
        <p className="eyebrow">OBD2 SOLUCIONES DIÉSEL</p>
        <h1>
          Control comercial,
          <br />
          claro y oportuno.
        </h1>
        <p className="muted">Ventas, clientes y cobranza en un solo lugar.</p>
        <form onSubmit={submit}>
          <label>
            Correo electrónico
          <input
            type="email"
            placeholder="nombre@empresa.com"
            value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label>
            Contraseña
          <input
            type="password"
            placeholder="Ingresa tu contraseña"
            value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button disabled={busy}>
            {busy ? "Ingresando…" : "Ingresar al portal"}
            <ChevronRight size={18} />
          </button>
        </form>
        <small>Acceso exclusivo para personal autorizado</small>
      </section>
      <aside className="login-art">
        <div>
          <span>OBD2 SD SYSTEM</span>
          <h2>
            Decisiones rápidas.
            <br />
            Seguimiento preciso.
          </h2>
          <p>
            Una visión completa de cada cliente, cada venta y cada compromiso.
          </p>
        </div>
      </aside>
    </main>
  );
}

function Modal({
  title,
  close,
  children,
}: {
  title: string;
  close: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="overlay" onMouseDown={close}>
      <section className="modal" onMouseDown={(e) => e.stopPropagation()}>
        <header>
          <h2>{title}</h2>
          <button className="icon" onClick={close}>
            <X />
          </button>
        </header>
        {children}
      </section>
    </div>
  );
}
function Empty({ text }: { text: string }) {
  return (
    <div className="empty">
      <ClipboardList />
      <h3>Aún no hay registros</h3>
      <p>{text}</p>
    </div>
  );
}

function App() {
  const [auth, setAuth] = useState(!!localStorage.getItem("obd2_token"));
  if (!auth) return <Login done={() => setAuth(true)} />;
  return (
    <Portal
      logout={() => {
        localStorage.removeItem("obd2_token");
        setAuth(false);
      }}
    />
  );
}
function Portal({ logout }: { logout: () => void }) {
  const [page, setPage] = useState<Page>("dashboard"),
    [mobile, setMobile] = useState(false);
  const nav = [
    ["dashboard", "Resumen", BarChart3],
    ["customers", "Clientes", Users],
    ["sales", "Ventas y servicios", BriefcaseBusiness],
    ["collections", "Cobranza", WalletCards],
    ["products", "Catálogo", Package],
  ] as const;
  return (
    <div className="shell">
      <aside className={mobile ? "sidebar open" : "sidebar"}>
        <div className="side-brand">
          <div className="brand-mark small">SD</div>
          <div>
            <b>OBD2 SD</b>
            <span>SYSTEM</span>
          </div>
          <button className="icon mobile" onClick={() => setMobile(false)}>
            <X />
          </button>
        </div>
        <nav>
          {nav.map(([id, label, Icon]) => (
            <button
              key={id}
              className={page === id ? "active" : ""}
              onClick={() => {
                setPage(id);
                setMobile(false);
              }}
            >
              <Icon size={20} />
              {label}
            </button>
          ))}
        </nav>
        <div className="side-foot">
          <span>Portal administrativo</span>
          <button onClick={logout}>
            <LogOut size={18} />
            Cerrar sesión
          </button>
        </div>
      </aside>
      <main className="content">
        <header className="topbar">
          <button className="icon mobile" onClick={() => setMobile(true)}>
            <Menu />
          </button>
          <div>
            <p>
              {new Intl.DateTimeFormat("es-MX", {
                weekday: "long",
                day: "numeric",
                month: "long",
              }).format(new Date())}
            </p>
            <h2>{nav.find((x) => x[0] === page)?.[1]}</h2>
          </div>
          <div className="avatar">AD</div>
        </header>
        <PageContent page={page} />
      </main>
    </div>
  );
}

function PageContent({ page }: { page: Page }) {
  if (page === "dashboard") return <DashboardPage />;
  if (page === "customers") return <Customers />;
  if (page === "sales") return <Sales />;
  if (page === "collections") return <Collections />;
  return <Products />;
}
function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null),
    [promises, setPromises] = useState<PromiseItem[]>([]);
  useEffect(() => {
    api<Dashboard>("/api/dashboard").then(setData);
    api<PromiseItem[]>("/api/promises").then(setPromises);
  }, []);
  const cards = [
    ["Por cobrar", data?.total_receivable, WalletCards, "blue"],
    ["Cartera vencida", data?.overdue, CalendarClock, "red"],
    ["Cobrado", data?.total_collected, BarChart3, "green"],
    ["Ventas acumuladas", data?.total_sales, BriefcaseBusiness, "gold"],
  ] as const;
  return (
    <>
      <section className="welcome">
        <div>
          <p className="eyebrow">CENTRO DE OPERACIÓN</p>
          <h1>Buenos días, Administrador</h1>
          <p>Esta es la situación comercial y de cobranza al momento.</p>
        </div>
        <div className="date-chip">Actualizado hoy</div>
      </section>
      <section className="stats">
        {cards.map(([label, value, Icon, color]) => (
          <article className={`stat ${color}`} key={label}>
            <div>
              <span>{label}</span>
              <strong>{money(value || 0)}</strong>
            </div>
            <Icon />
          </article>
        ))}
      </section>
      <section className="grid2">
        <article className="panel">
          <header>
            <div>
              <h3>Prioridades de cobranza</h3>
              <p>Compromisos que requieren atención</p>
            </div>
          </header>
          {promises
            .filter((x) => x.status === "pending")
            .slice(0, 5)
            .map((x) => (
              <div className="priority" key={x.id}>
                <span className={x.days_overdue ? "dot danger" : "dot"}></span>
                <div>
                  <b>{x.customer_name}</b>
                  <small>
                    {x.concept} ·{" "}
                    {x.days_overdue
                      ? `${x.days_overdue} días vencido`
                      : `vence ${x.due_date}`}
                  </small>
                </div>
                <strong>{money(x.amount)}</strong>
              </div>
            ))}
          {!promises.length && (
            <Empty text="Las fechas promesa aparecerán aquí." />
          )}
        </article>
        <article className="panel focus">
          <p className="eyebrow">ENFOQUE DE HOY</p>
          <h3>{data?.overdue_customers || 0} clientes requieren seguimiento</h3>
          <p>
            Hay {money(data?.due_today || 0)} con vencimiento hoy y{" "}
            {money(data?.due_next_7_days || 0)} comprometidos para los próximos
            7 días.
          </p>
          <div className="focus-numbers">
            <div>
              <strong>{data?.active_customers || 0}</strong>
              <span>Clientes activos</span>
            </div>
            <div>
              <strong>{data?.overdue_customers || 0}</strong>
              <span>Con mora</span>
            </div>
          </div>
        </article>
      </section>
    </>
  );
}

function Customers() {
  const [items, setItems] = useState<Customer[]>([]),
    [search, setSearch] = useState(""),
    [open, setOpen] = useState(false);
  const load = () =>
    api<Customer[]>(`/api/customers?search=${encodeURIComponent(search)}`).then(
      setItems,
    );
  useEffect(() => {
    void load();
  }, [search]);
  async function save(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    await api("/api/customers", {
      method: "POST",
      body: JSON.stringify({
        name: f.get("name"),
        company: f.get("company") || null,
        phone: f.get("phone"),
        email: f.get("email") || null,
        status: f.get("status"),
        notes: f.get("notes") || null,
      }),
    });
    setOpen(false);
    load();
  }
  return (
    <>
      <ActionHeader
        title="Clientes"
        text="Información comercial y financiera en una sola ficha."
        action="Nuevo cliente"
        click={() => setOpen(true)}
      />
      <div className="search">
        <Search />
        <input
          placeholder="Buscar por nombre, empresa o teléfono…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Cliente</th>
              <th>WhatsApp</th>
              <th>Estado</th>
              <th>Saldo</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id}>
                <td>
                  <b>{c.name}</b>
                  <small>{c.company || "Cliente particular"}</small>
                </td>
                <td>{c.phone}</td>
                <td>
                  <span className={`pill ${c.status}`}>
                    {c.status === "active"
                      ? "Activo"
                      : c.status === "prospect"
                        ? "Prospecto"
                        : "Inactivo"}
                  </span>
                </td>
                <td className={c.balance ? "owed" : ""}>{money(c.balance)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!items.length && (
          <Empty text="Registra el primer cliente para comenzar." />
        )}
      </div>
      {open && (
        <Modal title="Nuevo cliente" close={() => setOpen(false)}>
          <form className="form" onSubmit={save}>
            <Field label="Nombre o contacto" name="name" required />
            <Field label="Empresa" name="company" />
            <div className="row">
              <Field
                label="WhatsApp"
                name="phone"
                placeholder="523312345678"
                required
              />
              <Field label="Correo" name="email" type="email" />
            </div>
            <label>
              Estado
              <select name="status">
                <option value="prospect">Prospecto</option>
                <option value="active">Cliente activo</option>
                <option value="inactive">Inactivo</option>
              </select>
            </label>
            <label>
              Notas
              <textarea name="notes" rows={3} />
            </label>
            <Submit />
          </form>
        </Modal>
      )}
    </>
  );
}

function Sales() {
  const [items, setItems] = useState<Sale[]>([]),
    [customers, setCustomers] = useState<Customer[]>([]),
    [products, setProducts] = useState<Product[]>([]),
    [open, setOpen] = useState(false),
    [pay, setPay] = useState<Sale | null>(null);
  const load = () => api<Sale[]>("/api/sales").then(setItems);
  useEffect(() => {
    load();
    api<Customer[]>("/api/customers").then(setCustomers);
    api<Product[]>("/api/products").then(setProducts);
  }, []);
  async function save(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    await api("/api/sales", {
      method: "POST",
      body: JSON.stringify({
        customer_id: Number(f.get("customer_id")),
        product_id: f.get("product_id") ? Number(f.get("product_id")) : null,
        concept: f.get("concept"),
        vehicle: f.get("vehicle") || null,
        amount: Number(f.get("amount")),
        status: "won",
        sale_date: f.get("sale_date"),
        notes: f.get("notes") || null,
      }),
    });
    setOpen(false);
    load();
  }
  async function savePayment(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    await api("/api/payments", {
      method: "POST",
      body: JSON.stringify({
        sale_id: pay!.id,
        amount: Number(f.get("amount")),
        paid_at: f.get("paid_at"),
        method: f.get("method"),
        reference: f.get("reference") || null,
      }),
    });
    setPay(null);
    load();
  }
  return (
    <>
      <ActionHeader
        title="Ventas y servicios"
        text="Control de trabajos, importes y saldos pendientes."
        action="Registrar venta"
        click={() => setOpen(true)}
      />
      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Cliente / concepto</th>
              <th>Fecha</th>
              <th>Total</th>
              <th>Pagado</th>
              <th>Saldo</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((s) => (
              <tr key={s.id}>
                <td>
                  <b>{s.customer_name}</b>
                  <small>
                    {s.concept}
                    {s.vehicle ? ` · ${s.vehicle}` : ""}
                  </small>
                </td>
                <td>{s.sale_date}</td>
                <td>{money(s.amount)}</td>
                <td>{money(s.paid)}</td>
                <td className={s.balance ? "owed" : ""}>{money(s.balance)}</td>
                <td>
                  {s.balance > 0 && (
                    <button className="link" onClick={() => setPay(s)}>
                      Registrar pago
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!items.length && (
          <Empty text="Las ventas y servicios aparecerán aquí." />
        )}
      </div>
      {open && (
        <Modal title="Registrar venta o servicio" close={() => setOpen(false)}>
          <form className="form" onSubmit={save}>
            <label>
              Cliente
              <select name="customer_id" required>
                <option value="">Seleccionar…</option>
                {customers.map((c) => (
                  <option value={c.id} key={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Producto o servicio
              <select
                name="product_id"
                onChange={(e) => {
                  const p = products.find(
                    (x) => x.id === Number(e.target.value),
                  );
                  const form = e.currentTarget.form;
                  if (p && form) {
                    (
                      form.elements.namedItem("concept") as HTMLInputElement
                    ).value = p.name;
                    (
                      form.elements.namedItem("amount") as HTMLInputElement
                    ).value = String(p.price);
                  }
                }}
              >
                <option value="">Sin catálogo</option>
                {products.map((p) => (
                  <option value={p.id} key={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
            <Field label="Concepto" name="concept" required />
            <div className="row">
              <Field label="Unidad / vehículo" name="vehicle" />
              <Field label="Importe MXN" name="amount" type="number" required />
            </div>
            <Field
              label="Fecha"
              name="sale_date"
              type="date"
              defaultValue={today()}
              required
            />
            <label>
              Notas
              <textarea name="notes" rows={2} />
            </label>
            <Submit />
          </form>
        </Modal>
      )}
      {pay && (
        <Modal title="Registrar pago" close={() => setPay(null)}>
          <form className="form" onSubmit={savePayment}>
            <div className="notice">
              Saldo actual: <b>{money(pay.balance)}</b>
            </div>
            <div className="row">
              <Field
                label="Monto"
                name="amount"
                type="number"
                max={pay.balance}
                required
              />
              <Field
                label="Fecha"
                name="paid_at"
                type="date"
                defaultValue={today()}
                required
              />
            </div>
            <label>
              Método
              <select name="method">
                <option>Transferencia</option>
                <option>Efectivo</option>
                <option>Tarjeta</option>
                <option>Cheque</option>
              </select>
            </label>
            <Field label="Referencia" name="reference" />
            <Submit />
          </form>
        </Modal>
      )}
    </>
  );
}

function Collections() {
  const [items, setItems] = useState<PromiseItem[]>([]),
    [sales, setSales] = useState<Sale[]>([]),
    [open, setOpen] = useState(false);
  const load = () => api<PromiseItem[]>("/api/promises").then(setItems);
  useEffect(() => {
    load();
    api<Sale[]>("/api/sales").then((x) =>
      setSales(x.filter((s) => s.balance > 0)),
    );
  }, []);
  async function save(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    await api("/api/promises", {
      method: "POST",
      body: JSON.stringify({
        sale_id: Number(f.get("sale_id")),
        amount: Number(f.get("amount")),
        due_date: f.get("due_date"),
        status: "pending",
        notes: f.get("notes") || null,
      }),
    });
    setOpen(false);
    load();
  }
  return (
    <>
      <ActionHeader
        title="Cobranza"
        text="Promesas de pago ordenadas por prioridad."
        action="Nueva promesa"
        click={() => setOpen(true)}
      />
      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Cliente / concepto</th>
              <th>Fecha promesa</th>
              <th>Importe</th>
              <th>Situación</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((x) => (
              <tr key={x.id}>
                <td>
                  <b>{x.customer_name}</b>
                  <small>{x.concept}</small>
                </td>
                <td>{x.due_date}</td>
                <td>{money(x.amount)}</td>
                <td>
                  {x.status === "paid" ? (
                    <span className="pill active">Cumplida</span>
                  ) : x.days_overdue ? (
                    <span className="pill late">
                      {x.days_overdue} días de mora
                    </span>
                  ) : (
                    <span className="pill prospect">Pendiente</span>
                  )}
                </td>
                <td>
                  {x.status === "pending" && (
                    <button
                      className="link"
                      onClick={() =>
                        api(`/api/promises/${x.id}/paid`, {
                          method: "PATCH",
                        }).then(load)
                      }
                    >
                      Marcar cumplida
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!items.length && (
          <Empty text="Registra fechas promesa desde los saldos pendientes." />
        )}
      </div>
      {open && (
        <Modal title="Nueva promesa de pago" close={() => setOpen(false)}>
          <form className="form" onSubmit={save}>
            <label>
              Venta con saldo
              <select name="sale_id" required>
                <option value="">Seleccionar…</option>
                {sales.map((s) => (
                  <option value={s.id} key={s.id}>
                    {s.customer_name} · {s.concept} · {money(s.balance)}
                  </option>
                ))}
              </select>
            </label>
            <div className="row">
              <Field
                label="Monto prometido"
                name="amount"
                type="number"
                required
              />
              <Field
                label="Fecha promesa"
                name="due_date"
                type="date"
                required
              />
            </div>
            <label>
              Notas
              <textarea name="notes" rows={3} />
            </label>
            <Submit />
          </form>
        </Modal>
      )}
    </>
  );
}

function Products() {
  const [items, setItems] = useState<Product[]>([]),
    [open, setOpen] = useState(false);
  const load = () => api<Product[]>("/api/products").then(setItems);
  useEffect(() => {
    void load();
  }, []);
  async function save(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    await api("/api/products", {
      method: "POST",
      body: JSON.stringify({
        name: f.get("name"),
        category: f.get("category"),
        price: Number(f.get("price")),
        active: true,
      }),
    });
    setOpen(false);
    load();
  }
  return (
    <>
      <ActionHeader
        title="Catálogo"
        text="Productos y servicios disponibles para venta."
        action="Nuevo concepto"
        click={() => setOpen(true)}
      />
      <div className="cards-list">
        {items.map((p) => (
          <article key={p.id}>
            <div className="product-icon">
              <Package />
            </div>
            <div>
              <b>{p.name}</b>
              <span>{p.category}</span>
            </div>
            <strong>{money(p.price)}</strong>
          </article>
        ))}
        {!items.length && (
          <Empty text="Crea un catálogo sencillo para agilizar el registro de ventas." />
        )}
      </div>
      {open && (
        <Modal title="Nuevo producto o servicio" close={() => setOpen(false)}>
          <form className="form" onSubmit={save}>
            <Field label="Nombre" name="name" required />
            <div className="row">
              <label>
                Categoría
                <select name="category">
                  <option>Servicio</option>
                  <option>Producto</option>
                  <option>Licencia</option>
                  <option>Refacción</option>
                </select>
              </label>
              <Field
                label="Precio base"
                name="price"
                type="number"
                defaultValue="0"
                required
              />
            </div>
            <Submit />
          </form>
        </Modal>
      )}
    </>
  );
}

function ActionHeader({
  title,
  text,
  action,
  click,
}: {
  title: string;
  text: string;
  action: string;
  click: () => void;
}) {
  return (
    <section className="action-head">
      <div>
        <h1>{title}</h1>
        <p>{text}</p>
      </div>
      <button onClick={click}>
        <Plus size={18} />
        {action}
      </button>
    </section>
  );
}
function Field(
  p: React.InputHTMLAttributes<HTMLInputElement> & { label: string },
) {
  const { label, ...rest } = p;
  return (
    <label>
      {label}
      <input {...rest} />
    </label>
  );
}
function Submit() {
  return (
    <div className="form-actions">
      <button type="submit">Guardar registro</button>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
