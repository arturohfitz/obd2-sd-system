import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BarChart3,
  BriefcaseBusiness,
  CalendarClock,
  ChevronRight,
  ClipboardList,
  Clock,
  Download,
  FileText,
  LogOut,
  Menu,
  MessageCircle,
  Package,
  PenLine,
  Phone,
  Plus,
  Search,
  Users,
  WalletCards,
  X,
} from "lucide-react";
import { api, apiForm, downloadFile } from "./api";
import type { Customer, CustomerDetail, Dashboard, Product, PromiseItem, Sale } from "./types";
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
        <img
          className="brand-logo-icon"
          src="/brand/obd2-soluciones-diesel-icon.png"
          alt="OBD2 Soluciones Diésel"
        />
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
          <img
            className="brand-logo-horizontal"
            src="/brand/obd2-soluciones-diesel-logo.png"
            alt="OBD2 Soluciones Diésel"
          />
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
    [open, setOpen] = useState(false),
    [selected, setSelected] = useState<Customer | null>(null);
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
              <tr className="clickable-row" key={c.id} onClick={() => setSelected(c)}>
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
      {selected && (
        <CustomerProfile
          customerId={selected.id}
          close={() => setSelected(null)}
          changed={load}
        />
      )}
    </>
  );
}

function CustomerProfile({
  customerId,
  close,
  changed,
}: {
  customerId: number;
  close: () => void;
  changed: () => void;
}) {
  const [data, setData] = useState<CustomerDetail | null>(null),
    [tab, setTab] = useState<"account" | "history" | "files">("account"),
    [editing, setEditing] = useState(false),
    [addingActivity, setAddingActivity] = useState(false),
    [addingFile, setAddingFile] = useState(false);
  const load = () => api<CustomerDetail>(`/api/customers/${customerId}`).then(setData);
  useEffect(() => {
    void load();
  }, [customerId]);
  if (!data) return <div className="overlay"><div className="profile-loading">Cargando ficha…</div></div>;

  async function saveCustomer(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    await api(`/api/customers/${customerId}`, {
      method: "PATCH",
      body: JSON.stringify({
        name: form.get("name"), company: form.get("company") || null,
        phone: form.get("phone"), email: form.get("email") || null,
        status: form.get("status"), notes: form.get("notes") || null,
        next_follow_up: form.get("next_follow_up") || null,
      }),
    });
    setEditing(false); await load(); changed();
  }
  async function saveActivity(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault(); const form = new FormData(e.currentTarget);
    await api(`/api/customers/${customerId}/activities`, {method:"POST", body:JSON.stringify({activity_type:form.get("activity_type"),description:form.get("description"),follow_up_date:form.get("follow_up_date")||null})});
    setAddingActivity(false); await load(); changed();
  }
  async function saveFile(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault(); const form = new FormData(e.currentTarget);
    await apiForm(`/api/customers/${customerId}/files`, form);
    setAddingFile(false); await load();
  }
  async function cancelSale(sale: Sale) {
    if (!window.confirm(`¿Cancelar la venta "${sale.concept}"? El registro permanecerá en el historial.`)) return;
    try { await api(`/api/sales/${sale.id}/cancel`, {method:"PATCH"}); await load(); changed(); }
    catch (error) { window.alert((error as Error).message); }
  }
  const whatsappPhone = data.phone.startsWith("52") ? data.phone : `52${data.phone}`;
  return (
    <div className="overlay profile-overlay" onMouseDown={close}>
      <section className="customer-profile" onMouseDown={(e) => e.stopPropagation()}>
        <header className="profile-head">
          <div className="profile-avatar">{data.name.split(" ").map((part) => part[0]).slice(0,2).join("")}</div>
          <div className="profile-title"><span className={`pill ${data.status}`}>{data.status === "active" ? "Cliente activo" : data.status === "prospect" ? "Prospecto" : "Inactivo"}</span><h2>{data.name}</h2><p>{data.company || "Cliente particular"}</p></div>
          <div className="profile-actions">
            <a className="whatsapp-btn" href={`https://wa.me/${whatsappPhone}`} target="_blank" rel="noreferrer"><MessageCircle size={17}/>WhatsApp</a>
            <button className="secondary-btn" onClick={() => setEditing(true)}><PenLine size={17}/>Editar</button>
            <button className="icon" onClick={close}><X/></button>
          </div>
        </header>
        <div className="profile-contact"><span><Phone size={15}/>{data.phone}</span><span>{data.email || "Sin correo registrado"}</span>{data.next_follow_up && <span><Clock size={15}/>Seguimiento: {data.next_follow_up}</span>}</div>
        <section className="profile-metrics"><div><span>Ventas</span><strong>{money(data.sales.filter((sale) => sale.status === "won").reduce((sum, sale) => sum + Number(sale.amount), 0))}</strong></div><div><span>Pagado</span><strong>{money(data.sales.reduce((sum, sale) => sum + Number(sale.paid), 0))}</strong></div><div className="metric-owed"><span>Saldo pendiente</span><strong>{money(data.balance)}</strong></div><div><span>Operaciones</span><strong>{data.sales.length}</strong></div></section>
        <nav className="profile-tabs"><button className={tab === "account" ? "active" : ""} onClick={() => setTab("account")}>Estado de cuenta</button><button className={tab === "history" ? "active" : ""} onClick={() => setTab("history")}>Historial <span>{data.activities.length}</span></button><button className={tab === "files" ? "active" : ""} onClick={() => setTab("files")}>Documentos <span>{data.files.length}</span></button></nav>
        <div className="profile-body">
          {tab === "account" && <><div className="section-heading"><div><h3>Ventas y servicios</h3><p>Movimientos y saldos del cliente.</p></div></div><div className="account-list">{data.sales.map((sale) => <article className={sale.status === "cancelled" ? "cancelled" : ""} key={sale.id}><div><b>{sale.concept}</b><small>{sale.sale_date}{sale.vehicle ? ` · ${sale.vehicle}` : ""}</small></div><div><span>Total</span><b>{money(sale.amount)}</b></div><div><span>Pagado</span><b>{money(sale.paid)}</b></div><div><span>Saldo</span><b className={sale.balance ? "owed" : ""}>{money(sale.balance)}</b></div>{sale.status === "cancelled" ? <span className="pill inactive">Cancelada</span> : sale.paid === 0 && <button className="link danger-link" onClick={() => cancelSale(sale)}>Cancelar</button>}</article>)}{!data.sales.length && <Empty text="Este cliente todavía no tiene operaciones."/>}</div></>}
          {tab === "history" && <><div className="section-heading"><div><h3>Historial de seguimiento</h3><p>Notas, contactos y cambios de la cuenta.</p></div><button onClick={() => setAddingActivity(true)}><Plus size={16}/>Agregar actividad</button></div><div className="timeline">{data.activities.map((item) => <article key={item.id}><div className={`timeline-icon ${item.activity_type}`}><Clock size={15}/></div><div><b>{item.description}</b><p>{item.user_name} · {new Date(item.created_at).toLocaleString("es-MX")}</p>{item.follow_up_date && <span>Próximo seguimiento: {item.follow_up_date}</span>}</div></article>)}{!data.activities.length && <Empty text="Agrega la primera nota de seguimiento."/>}</div></>}
          {tab === "files" && <><div className="section-heading"><div><h3>Documentos privados</h3><p>Comprobantes, cotizaciones y evidencias.</p></div><button onClick={() => setAddingFile(true)}><Plus size={16}/>Adjuntar documento</button></div><div className="file-list">{data.files.map((file) => <article key={file.id}><div className="file-icon"><FileText/></div><div><b>{file.original_name}</b><small>{file.description || "Sin descripción"} · {(file.size / 1024).toFixed(1)} KB</small></div><button className="icon" title="Descargar" onClick={() => downloadFile(`/api/customer-files/${file.id}/download`, file.original_name)}><Download/></button></article>)}{!data.files.length && <Empty text="No hay documentos adjuntos."/>}</div></>}
        </div>
      </section>
      {editing && <Modal title="Editar cliente" close={() => setEditing(false)}><form className="form" onSubmit={saveCustomer}><Field label="Nombre o contacto" name="name" defaultValue={data.name} required/><Field label="Empresa" name="company" defaultValue={data.company}/><div className="row"><Field label="WhatsApp" name="phone" defaultValue={data.phone} required/><Field label="Correo" name="email" type="email" defaultValue={data.email}/></div><label>Estado<select name="status" defaultValue={data.status}><option value="prospect">Prospecto</option><option value="active">Cliente activo</option><option value="inactive">Inactivo</option></select></label><Field label="Próximo seguimiento" name="next_follow_up" type="date" defaultValue={data.next_follow_up}/><label>Notas<textarea name="notes" rows={3} defaultValue={data.notes}/></label><Submit/></form></Modal>}
      {addingActivity && <Modal title="Agregar actividad" close={() => setAddingActivity(false)}><form className="form" onSubmit={saveActivity}><label>Tipo<select name="activity_type"><option value="note">Nota</option><option value="call">Llamada</option><option value="whatsapp">WhatsApp</option><option value="visit">Visita</option><option value="promise">Compromiso</option></select></label><label>Descripción<textarea name="description" rows={4} required placeholder="Resultado del contacto o información relevante…"/></label><Field label="Próximo seguimiento" name="follow_up_date" type="date"/><Submit/></form></Modal>}
      {addingFile && <Modal title="Adjuntar documento" close={() => setAddingFile(false)}><form className="form" onSubmit={saveFile}><label>Archivo<input name="file" type="file" accept=".pdf,.jpg,.jpeg,.png,.webp" required/></label><Field label="Descripción" name="description" placeholder="Ej. Comprobante de transferencia"/><small className="form-help">PDF o imagen, máximo 10 MB.</small><Submit/></form></Modal>}
    </div>
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
