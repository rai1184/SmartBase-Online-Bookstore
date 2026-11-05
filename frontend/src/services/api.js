import { formatBook } from "../utils/formatters";

const API_BASE_URL = "http://localhost:5001/api";

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