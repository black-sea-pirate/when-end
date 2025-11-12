// API client for backend communication

const API_BASE = "/api";

export interface Event {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  event_date: string;
  repeat_interval: "none" | "day" | "week" | "month" | "year";
  timezone: string | null;
  next_occurrence: string | null;
  effective_due_at: string;
  remaining_seconds: number;
  color_bucket:
    | "RED"
    | "ORANGE"
    | "YELLOW"
    | "GREEN"
    | "CYAN"
    | "BLUE"
    | "PURPLE"
    | null;
  is_overdue: boolean;
  attachments: Attachment[];
  created_at: string;
  updated_at: string;
}

export interface Attachment {
  id: string;
  name: string;
  mime: string;
  size: number;
  url: string;
  thumb_url: string | null;
  width: number | null;
  height: number | null;
  duration: number | null;
}

export interface EventListResponse {
  server_now: string;
  items: Event[];
  next_cursor: string | null;
}

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateEventData {
  title: string;
  description?: string | null;
  event_date: string;
  repeat_interval: "none" | "day" | "week" | "month" | "year";
  timezone?: string | null;
}

export interface UpdateEventData {
  title?: string;
  description?: string | null;
  event_date?: string;
  repeat_interval?: "none" | "day" | "week" | "month" | "year";
  timezone?: string | null;
}

export interface SharePreview {
  title: string;
  description: string | null;
  event_date: string;
  repeat_interval: string;
  timezone: string | null;
  has_attachments: boolean;
  created_at: string;
}

export interface ShareCreateResponse {
  share_url: string;
  token: string;
  expires_at: string | null;
}

class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      credentials: "include", // Include cookies
    });

    if (!response.ok) {
      let error;
      try {
        error = await response.json();
      } catch {
        error = { detail: "Request failed" };
      }
      throw new Error(error.detail || `Request failed: ${response.statusText}`);
    }
    if (response.status === 204) return undefined as unknown as T;
    return response.json();
  }

  // Auth
  async getCurrentUser(): Promise<User> {
    return this.request<User>("/auth/me");
  }

  async logout(): Promise<void> {
    await this.request("/auth/logout", { method: "POST" });
  }

  async refreshToken(): Promise<void> {
    await this.request("/auth/refresh", { method: "POST" });
  }

  // Events
  async listEvents(params?: {
    q?: string;
    include_overdue?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<EventListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.q) searchParams.append("q", params.q);
    if (params?.include_overdue !== undefined)
      searchParams.append("include_overdue", params.include_overdue.toString());
    if (params?.limit) searchParams.append("limit", params.limit.toString());
    if (params?.offset) searchParams.append("offset", params.offset.toString());

    const query = searchParams.toString();
    return this.request<EventListResponse>(
      `/events${query ? `?${query}` : ""}`
    );
  }

  async getEvent(id: string): Promise<Event> {
    return this.request<Event>(`/events/${id}`);
  }

  async createEvent(data: CreateEventData): Promise<Event> {
    return this.request<Event>("/events", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateEvent(id: string, data: UpdateEventData): Promise<Event> {
    return this.request<Event>(`/events/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteEvent(id: string): Promise<void> {
    await this.request(`/events/${id}`, { method: "DELETE" });
  }

  async uploadAttachment(
    eventId: string,
    file: File
  ): Promise<{ id: string; message: string }> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/events/${eventId}/attachments`, {
      method: "POST",
      body: formData,
      credentials: "include",
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "Upload failed" }));
      throw new Error(error.detail || "Upload failed");
    }

    return response.json();
  }

  async deleteAttachment(eventId: string, attachmentId: string): Promise<void> {
    await this.request(`/events/${eventId}/attachments/${attachmentId}`, {
      method: "DELETE",
    });
  }

  // Share
  async createShareToken(eventId: string): Promise<ShareCreateResponse> {
    return this.request<ShareCreateResponse>(`/events/${eventId}/share`, {
      method: "POST",
    });
  }

  async getSharePreview(token: string): Promise<SharePreview> {
    return this.request<SharePreview>(`/share/${token}`);
  }

  async importSharedEvent(
    token: string,
    includeAttachments: boolean = false
  ): Promise<{ event_id: string; message: string }> {
    return this.request(`/share/${token}/import`, {
      method: "POST",
      body: JSON.stringify({ include_attachments: includeAttachments }),
    });
  }
}

export const apiClient = new ApiClient();
