import { formatBook } from "../utils/formatters";

const API_BASE_URL = "/api";

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function authRequest(path, body) {
  const response = await fetch(`${API_BASE_URL}/auth/${path}`, {
    method: body === undefined ? "GET" : "POST",
    credentials: "include",
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json();

  if (!response.ok) {
    throw new ApiError(
      data.message || `Authentication request failed (HTTP ${response.status}).`,
      response.status,
    );
  }

  return data;
}

export async function loginApi(username, password) {
  const data = await authRequest("login", { username, password });
  return data.user;
}

export function googleLoginApi(idToken) {
  return authRequest("google", { id_token: idToken });
}

export async function accountSetupApi(accountSetupToken, username, password) {
  const data = await authRequest("account-setup", {
    account_setup_token: accountSetupToken,
    username,
    password,
  });
  return data.user;
}

export async function getCurrentUserApi() {
  try {
    const data = await authRequest("me");
    return data.user;
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return null;
    }
    throw error;
  }
}

export function logoutApi() {
  return authRequest("logout", {});
}

// Returns all books from DB
export async function fetchBooksFromApi() {
  const response = await fetch(`${API_BASE_URL}/books`);
  if (!response.ok) {
    throw new Error(`Could not load books (HTTP ${response.status}).`);
  }

  const data = await response.json();
  if (!Array.isArray(data)) {
    throw new Error("The books API returned an unexpected response.");
  }

  return data.map(formatBook);
}

// Given parameters, return object storing exact matches and alternative matches
export async function searchBooksApi(params) {
  const response = await fetch(`${API_BASE_URL}/books/search?${params.toString()}`);
  if (!response.ok) {
    throw new Error("Failed to fetch search results from the server.");
  }

  const data = await response.json();
  return {
    exact_matches: (data.exact_matches || []).map(formatBook),
    alternative_matches: (data.alternative_matches || []).map(formatBook),
  };
}

export async function checkHealthApi() {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error();
  }
  const data = await response.json();
  return data.message || "Online";
}