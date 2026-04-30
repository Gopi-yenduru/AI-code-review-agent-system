/**
 * Axios API client for the AI Code Review Agent backend.
 * All requests go through /api/v1 prefix.
 */
import axios from 'axios';

const API_BASE = '/api/v1';

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// ── Reviews ──────────────────────────────────────────────────
export const fetchReviews = (params = {}) =>
  client.get('/reviews', { params }).then(r => r.data);

export const fetchReviewById = (id) =>
  client.get(`/reviews/${id}`).then(r => r.data);

// ── Analytics ────────────────────────────────────────────────
export const fetchOverviewStats = () =>
  client.get('/analytics/overview').then(r => r.data);

export const fetchDeveloperStats = (username) =>
  client.get(`/analytics/developer/${username}`).then(r => r.data);

export const fetchRepoStats = (repoName) =>
  client.get(`/analytics/repo/${repoName}`).then(r => r.data);

export default client;
