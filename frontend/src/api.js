const API_URL = import.meta.env.VITE_API_URL || "/api";

export async function api(path, options = {}) {
  const token = localStorage.getItem("todo_token");
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) localStorage.removeItem("todo_token");
    throw new Error(data.message || "Wystąpił błąd połączenia z serwerem.");
  }
  return data;
}
