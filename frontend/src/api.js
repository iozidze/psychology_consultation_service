const API_URL = import.meta.env.VITE_API_URL || "https://psychology-consultation-service-1.onrender.com";

function getErrorMessage(errorBody) {
  if (!errorBody) {
    return "Ошибка запроса";
  }
  if (typeof errorBody.detail === "string") {
    return errorBody.detail;
  }
  if (Array.isArray(errorBody.detail)) {
    return errorBody.detail.map((item) => item.msg).join("; ");
  }
  return "Ошибка запроса";
}

export async function apiRequest(path, { method = "GET", body, token } = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(getErrorMessage(data));
  }
  return data;
}

export { API_URL };
