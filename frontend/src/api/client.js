/**
 * API client for the AI Code Review Agent backend.
 */
const BASE_URL = window.APP_CONFIG?.apiUrl && window.APP_CONFIG.apiUrl !== '__API_URL__'
  ? window.APP_CONFIG.apiUrl 
  : (import.meta.env.VITE_API_URL || 'http://localhost:8000');
console.log("API BASE URL:", BASE_URL);

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}/api/v1${endpoint}`;
  try {
    const response = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    
    if (!response.ok) {
      console.error("API error:", response.status, await response.text());
      return { success: false, _error: "API error" };
    }
    
    return await response.json();
  } catch (error) {
    console.error(`Fetch failed for ${endpoint}:`, error);
    throw error;
  }
}

// ── Reviews ──────────────────────────────────────────────────
export const fetchReviews = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/reviews${qs ? `?${qs}` : ''}`);
};

export const fetchReviewById = (id) => request(`/reviews/${id}`);

// ── Analytics ────────────────────────────────────────────────
export const fetchOverviewStats = () => request('/analytics/overview');

export const fetchDeveloperStats = (username) => request(`/analytics/developer/${username}`);

export const fetchRepoStats = (repoName) => request(`/analytics/repo/${repoName}`);
