const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface ApiError {
  detail: string;
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Don't set Content-Type for FormData (browser sets it with boundary)
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }

  return res.json();
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),

  post: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, {
      method: "POST",
      body: data instanceof FormData ? data : JSON.stringify(data),
    }),

  put: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: <T>(endpoint: string) =>
    request<T>(endpoint, {
      method: "DELETE",
    }),

  upload: <T>(endpoint: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<T>(endpoint, {
      method: "POST",
      body: formData,
    });
  },
};

// ── Auth ──
export const authApi = {
  login: (email: string, password: string) =>
    request<{ access_token: string; token_type: string }>(
      "/api/auth/token",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
        headers: { "Content-Type": "application/json" },
      }
    ),

  register: (email: string, password: string, full_name: string) =>
    request<{ id: number; email: string }>(
      "/api/auth/register",
      {
        method: "POST",
        body: JSON.stringify({ email, password, full_name }),
        headers: { "Content-Type": "application/json" },
      }
    ),
};

// ── Jobs ──
export const jobsApi = {
  list: (params?: string) =>
    api.get<{ items: Job[]; total: number }>(`/api/jobs/${params || ""}`),
  scrape: () =>
    api.post<{ message: string }>("/api/jobs/scrape", { query: "auto", location: "auto" }),
  scraperRuns: (limit = 20) =>
    api.get<ScraperRun[]>(`/api/jobs/scraper-runs?limit=${limit}`),
  clear: () => api.delete<{ message: string }>("/api/jobs/clear"),
};

// ── Matches ──
export const matchesApi = {
  list: (params?: string) =>
    api.get<{ items: Match[]; total: number }>(`/api/matches/${params || ""}`),
  approve: (id: number) =>
    api.post<{ id: number; status: string }>(`/api/matches/${id}/approve`),
  reject: (id: number) =>
    api.post<{ id: number; status: string }>(`/api/matches/${id}/reject`),
};

// ── Applications ──
export const applicationsApi = {
  list: (params?: string) =>
    api.get<{ items: Application[]; total: number }>(
      `/api/applications/${params || ""}`
    ),
  retry: (id: number) =>
    api.post<{ message: string }>(`/api/applications/${id}/retry`),
};

// ── Resumes ──
export const resumesApi = {
  list: (params?: string) =>
    api.get<{ items: Resume[]; total: number }>(`/api/resumes/${params || ""}`),
  upload: (file: File) => api.upload<Resume>("/api/resumes/upload", file),
  delete: (id: number) =>
    api.post<{ message: string }>(`/api/resumes/${id}/delete`),
};

// ── Settings ──
export const settingsApi = {
  getPreferences: () => api.get<Preference>("/api/settings/preferences"),
  updatePreferences: (data: PreferenceUpdate) =>
    api.put<Preference>("/api/settings/preferences", data),
  getConfig: () => api.get<Record<string, string>>("/api/settings/config"),
  updateConfig: (data: Record<string, string>) =>
    api.put<Record<string, string>>("/api/settings/config", data),
};

// ── Types ──
export interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  url: string;
  source: string;
  job_type: string;
  experience_level: string;
  remote_status: string;
  salary_min: number | null;
  salary_max: number | null;
  description: string;
  extracted_skills: string;
  created_at: string;
}

export interface Match {
  id: number;
  job_id: number;
  resume_id: number;
  semantic_score: number;
  skill_score: number;
  title_score: number;
  location_score: number;
  final_score: number;
  status: string;
  created_at: string;
  job_title: string | null;
  job_company: string | null;
  job_url: string | null;
}

export interface Application {
  id: number;
  match_id: number;
  status: string;
  handler_type: string;
  method: string;
  retry_count: number;
  max_retries: number;
  error_log: string | null;
  created_at: string;
}

export interface Resume {
  id: number;
  user_id: number;
  file_name: string;
  version: number;
  structured_data: string;
  created_at: string;
}

export interface Preference {
  id: number;
  desired_titles: string;
  desired_locations: string;
  excluded_companies: string;
  min_salary: number | null;
  remote_only: boolean;
  country: string;
  workplace_type: string;
}

export interface PreferenceUpdate {
  desired_titles: string[];
  desired_locations: string[];
  excluded_companies: string[];
  min_salary: number | null;
  remote_only: boolean;
  country: string;
  workplace_type: string;
}

export interface ScraperRun {
  id: number;
  provider: string;
  status: string;
  jobs_found: number;
  jobs_new: number;
  duration_seconds: number;
  error_log: string | null;
  started_at: string | null;
}
