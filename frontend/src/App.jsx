import { useEffect, useState } from "react";
import { api } from "./api";

function AuthScreen({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", email: "", login: "", password: "" });
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [busy, setBusy] = useState(false);

  const change = (e) => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
    setFieldErrors({ ...fieldErrors, [name]: "" });
  };
  function validate() {
    const errors = {};
    if (mode === "register") {
      if (form.username.trim().length < 3) errors.username = "Nazwa użytkownika musi mieć co najmniej 3 znaki.";
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) errors.email = "Podaj poprawny adres e-mail.";
    } else if (!form.login.trim()) {
      errors.login = "Podaj e-mail lub nazwę użytkownika.";
    }
    if (form.password.length < 8) errors.password = "Hasło musi mieć co najmniej 8 znaków.";
    return errors;
  }
  async function submit(e) {
    e.preventDefault();
    const errors = validate();
    setFieldErrors(errors);
    setError("");
    if (Object.keys(errors).length) return;
    setBusy(true);
    try {
      const body = mode === "login"
        ? { login: form.login, password: form.password }
        : { username: form.username, email: form.email, password: form.password };
      const result = await api(`/auth/${mode}`, { method: "POST", body: JSON.stringify(body) });
      localStorage.setItem("todo_token", result.token);
      onAuthenticated(result.user);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return <main className="auth-layout">
    <section className="auth-aside">
      <div className="brand brand-light"><span className="brand-mark">✓</span> taskly</div>
      <div><p className="eyebrow">MNIEJ CHAOSU, WIĘCEJ SPOKOJU</p><h1>Wszystkie Twoje sprawy. W jednym miejscu.</h1><p className="aside-copy">Zaplanuj dzień, uporządkuj priorytety i odhaczaj kolejne małe zwycięstwa.</p></div>
      <div className="aside-note">✦ &nbsp; Jeden krok na raz. Dasz radę.</div>
    </section>
    <section className="auth-main">
      <div className="auth-card">
        <div className="brand"><span className="brand-mark">✓</span> taskly</div>
        <p className="eyebrow">WITAJ W TASKLY</p>
        <h2>{mode === "login" ? "Miło Cię widzieć" : "Utwórz konto"}</h2>
        <p className="muted">{mode === "login" ? "Zaloguj się, aby wrócić do swoich zadań." : "Załóż konto i zacznij planować swój dzień."}</p>
        <div className="auth-tabs"><button type="button" className={mode === "login" ? "active" : ""} onClick={() => {setMode("login");setError("");setFieldErrors({});}}>Logowanie</button><button type="button" className={mode === "register" ? "active" : ""} onClick={() => {setMode("register");setError("");setFieldErrors({});}}>Rejestracja</button></div>
        <form noValidate onSubmit={submit} className="form-stack">
          {mode === "register" ? <>
            <label>Nazwa użytkownika<input name="username" value={form.username} onChange={change} placeholder="np. janek123" maxLength="40" required />{fieldErrors.username && <span className="field-error">{fieldErrors.username}</span>}</label>
            <label>Adres e-mail<input type="email" name="email" value={form.email} onChange={change} placeholder="jan@example.com" required />{fieldErrors.email && <span className="field-error">{fieldErrors.email}</span>}</label>
          </> : <label>E-mail lub nazwa użytkownika<input name="login" value={form.login} onChange={change} placeholder="Wpisz swój login" required />{fieldErrors.login && <span className="field-error">{fieldErrors.login}</span>}</label>}
          <label>Hasło<input type="password" name="password" value={form.password} onChange={change} placeholder="Minimum 8 znaków" minLength="8" required />{fieldErrors.password && <span className="field-error">{fieldErrors.password}</span>}</label>
          {error && <p className="error" role="alert">{error}</p>}
          <button className="primary-btn" disabled={busy}>{busy ? "Chwileczkę..." : mode === "login" ? "Zaloguj się →" : "Utwórz konto →"}</button>
        </form>
        <p className="tiny muted">Twoje zadania są prywatne i dostępne tylko po zalogowaniu.</p>
      </div>
    </section>
  </main>;
}

function Dashboard({ user, onLogout }) {
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);
  const [busyAction, setBusyAction] = useState("");

  async function loadTasks() {
    try { const data = await api("/tasks"); setTasks(data.tasks); setError(""); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }
  useEffect(() => { loadTasks(); }, []);

  async function addTask(e) {
    e.preventDefault();
    const trimmedTitle = title.trim();
    const trimmedDescription = description.trim();
    if (!trimmedTitle) {
      setError("Tytuł zadania jest wymagany.");
      return;
    }
    if (trimmedTitle.length > 160 || trimmedDescription.length > 1000) {
      setError("Tytuł może mieć 160 znaków, a opis 1000 znaków.");
      return;
    }
    setBusyAction("add"); setError(""); setSuccess("");
    try {
      const data = await api("/tasks", { method: "POST", body: JSON.stringify({ title: trimmedTitle, description: trimmedDescription }) });
      setTasks(current => [data.task, ...current]); setTitle(""); setDescription(""); setSuccess("Zadanie zostało dodane.");
    } catch (e) { setError(e.message); }
    finally { setBusyAction(""); }
  }
  async function toggleTask(task) {
    setBusyAction(`toggle-${task.id}`); setError(""); setSuccess("");
    try {
      const data = await api(`/tasks/${task.id}`, { method: "PATCH", body: JSON.stringify({ completed: !task.completed }) });
      setTasks(current => current.map(t => t.id === task.id ? data.task : t)); setSuccess("Status zadania został zmieniony.");
    } catch (e) { setError(e.message); }
    finally { setBusyAction(""); }
  }
  async function deleteTask(id) {
    setBusyAction(`delete-${id}`); setError(""); setSuccess("");
    try { await api(`/tasks/${id}`, { method: "DELETE" }); setTasks(current => current.filter(t => t.id !== id)); setSuccess("Zadanie zostało usunięte."); }
    catch (e) { setError(e.message); }
    finally { setBusyAction(""); }
  }
  async function saveEdit(e) {
    e.preventDefault();
    const trimmedTitle = editing.title.trim();
    const trimmedDescription = editing.description.trim();
    if (!trimmedTitle) { setError("Tytuł zadania jest wymagany."); return; }
    if (trimmedTitle.length > 160 || trimmedDescription.length > 1000) { setError("Tytuł może mieć 160 znaków, a opis 1000 znaków."); return; }
    setBusyAction(`edit-${editing.id}`); setError(""); setSuccess("");
    try {
      const data = await api(`/tasks/${editing.id}`, { method: "PATCH", body: JSON.stringify({ title: trimmedTitle, description: trimmedDescription }) });
      setTasks(current => current.map(t => t.id === editing.id ? data.task : t)); setEditing(null); setSuccess("Zadanie zostało zapisane.");
    } catch (e) { setError(e.message); }
    finally { setBusyAction(""); }
  }

  const visible = tasks.filter(t => filter === "all" || (filter === "active" && !t.completed) || (filter === "done" && t.completed));
  const completed = tasks.filter(t => t.completed).length;
  const progress = tasks.length ? Math.round(completed / tasks.length * 100) : 0;

  return <div className="dashboard">
    <header className="topbar"><div className="brand"><span className="brand-mark">✓</span> taskly</div><div className="user-menu"><span className="avatar">{user.username.slice(0,1).toUpperCase()}</span><span>{user.username}</span><button className="logout" onClick={onLogout}>Wyloguj</button></div></header>
    <main className="dashboard-main">
      <div className="welcome"><div><p className="eyebrow">TWÓJ OSOBISTY PLANER</p><h1>Cześć, {user.username} <span></span></h1><p className="muted">Małe kroki prowadzą do wielkich rzeczy. Co dziś zrobisz?</p></div><div className="date-chip">{new Intl.DateTimeFormat("pl-PL", { weekday: "long", day: "numeric", month: "long" }).format(new Date())}</div></div>
      <section className="stats"><div className="stat-card"><span className="stat-icon lavender">▤</span><div><strong>{tasks.length}</strong><span>Wszystkie zadania</span></div></div><div className="stat-card"><span className="stat-icon peach">◷</span><div><strong>{tasks.length - completed}</strong><span>Do zrobienia</span></div></div><div className="stat-card"><span className="stat-icon mint">✓</span><div><strong>{completed}</strong><span>Ukończone</span></div></div></section>
      <section className="content-grid">
        <div className="task-panel">
          <div className="section-heading"><div><h2>Twoje zadania</h2><p className="muted">Zamień plany w działanie.</p></div><span className="count-pill">{visible.length} zadań</span></div>
          <div className="filters"><button className={filter==="all"?"selected":""} onClick={()=>setFilter("all")}>Wszystkie</button><button className={filter==="active"?"selected":""} onClick={()=>setFilter("active")}>Aktywne</button><button className={filter==="done"?"selected":""} onClick={()=>setFilter("done")}>Ukończone</button></div>
          {error && <p className="error" role="alert">{error}</p>}
          {success && <p className="success" role="status">{success}</p>}
          {loading ? <p className="empty">Ładowanie zadań...</p> : visible.length === 0 ? <div className="empty-state"><div>✧</div><h3>{tasks.length ? "Tu jest teraz spokojnie" : "Zacznij od pierwszego zadania"}</h3><p className="muted">{tasks.length ? "Nie ma zadań w tym widoku." : "Dodaj zadanie w formularzu obok, aby ruszyć z miejsca."}</p></div> :
            <div className="task-list">{visible.map(task => <article className={`task-row ${task.completed?"is-done":""}`} key={task.id}>
              <button className={`check ${task.completed?"checked":""}`} onClick={()=>toggleTask(task)} disabled={busyAction === `toggle-${task.id}`} aria-label="Zmień status">{task.completed?"✓":""}</button>
              <div className="task-info"><strong>{task.title}</strong>{task.description && <p>{task.description}</p>}</div>
              <div className="task-actions"><button onClick={()=>setEditing({...task})} disabled={Boolean(busyAction)} aria-label="Edytuj">✎</button><button onClick={()=>deleteTask(task.id)} disabled={Boolean(busyAction)} aria-label="Usuń">{busyAction === `delete-${task.id}` ? "…" : "×"}</button></div>
            </article>)}</div>}
        </div>
        <aside className="side-column">
          <form noValidate className="add-panel" onSubmit={addTask}><p className="eyebrow">NOWY PLAN</p><h2>Dodaj zadanie</h2><label>Tytuł zadania<input value={title} onChange={e=>setTitle(e.target.value)} maxLength="160" placeholder="Co masz do zrobienia?" required /></label><label>Opis <span className="optional">opcjonalnie</span><textarea value={description} onChange={e=>setDescription(e.target.value)} maxLength="1000" rows="3" placeholder="Dodaj kilka szczegółów..." /></label><button className="primary-btn" disabled={busyAction === "add"}>{busyAction === "add" ? "Dodawanie..." : "+ Dodaj zadanie"}</button></form>
          <div className="progress-panel"><div className="progress-title"><h3>Twój postęp</h3><strong>{progress}%</strong></div><div className="progress-track"><span style={{width:`${progress}%`}} /></div><p className="muted">{completed} z {tasks.length} zadań ukończonych. Tak trzymaj!</p></div>
        </aside>
      </section>
      <footer>Taskly · Twój dzień, Twoje tempo.</footer>
    </main>
    {editing && <div className="modal-backdrop" onClick={()=>setEditing(null)}><form noValidate className="edit-modal" onSubmit={saveEdit} onClick={e=>e.stopPropagation()}><h2>Edytuj zadanie</h2><label>Tytuł<input value={editing.title} onChange={e=>setEditing({...editing,title:e.target.value})} required maxLength="160" /></label><label>Opis<textarea value={editing.description} onChange={e=>setEditing({...editing,description:e.target.value})} rows="4" maxLength="1000" /></label><div className="modal-actions"><button type="button" className="secondary-btn" onClick={()=>setEditing(null)}>Anuluj</button><button className="primary-btn" disabled={busyAction === `edit-${editing.id}`}>{busyAction === `edit-${editing.id}` ? "Zapisywanie..." : "Zapisz zmiany"}</button></div></form></div>}
  </div>;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(Boolean(localStorage.getItem("todo_token")));
  useEffect(() => {
    if (!localStorage.getItem("todo_token")) return;
    api("/auth/me").then(data => setUser(data.user)).catch(() => localStorage.removeItem("todo_token")).finally(() => setChecking(false));
  }, []);
  function logout() { localStorage.removeItem("todo_token"); setUser(null); }
  if (checking) return <div className="loading-screen">Taskly ładuje Twój planer...</div>;
  return user ? <Dashboard user={user} onLogout={logout} /> : <AuthScreen onAuthenticated={setUser} />;
}
