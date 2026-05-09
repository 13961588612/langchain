const API_BASE = "/api";

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

interface Agent {
  id: string;
  name: string;
  description?: string;
  system_prompt?: string;
  model_provider: string;
  model_name: string;
  model_parameters?: string;
  is_active: boolean;
  soul_config?: string;
  profile_config?: string;
  created_at: string;
  updated_at: string;
}

interface Conversation {
  id: string;
  agent_id: string;
  thread_id: string;
  title?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface Message {
  id: string;
  conversation_id: string;
  role: string;
  content: string;
  created_at: string;
}

async function request<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // Agents
  listAgents: (params?: {
    page?: number;
    page_size?: number;
    search?: string;
    is_active?: boolean;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set("page", String(params.page));
    if (params?.page_size) searchParams.set("page_size", String(params.page_size));
    if (params?.search) searchParams.set("search", params.search);
    if (params?.is_active !== undefined)
      searchParams.set("is_active", String(params.is_active));
    const qs = searchParams.toString();
    return request<PaginatedResponse<Agent>>(`/agents${qs ? `?${qs}` : ""}`);
  },

  getAgent: (id: string) => request<Agent>(`/agents/${id}`),

  createAgent: (data: {
    name: string;
    description?: string;
    system_prompt?: string;
    model_provider?: string;
    model_name?: string;
    model_parameters?: string;
    soul_config?: string;
    profile_config?: string;
  }) =>
    request<Agent>("/agents", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateAgent: (
    id: string,
    data: Record<string, unknown>
  ) =>
    request<Agent>(`/agents/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteAgent: (id: string) =>
    request<void>(`/agents/${id}`, { method: "DELETE" }),

  toggleAgent: (id: string, active: boolean) =>
    request<Agent>(`/agents/${id}/activate?active=${active}`, { method: "POST" }),

  // Conversations
  createConversation: (agentId: string, title?: string) =>
    request<Conversation>("/conversations", {
      method: "POST",
      body: JSON.stringify({ agent_id: agentId, title }),
    }),

  listConversations: (params?: {
    agent_id?: string;
    page?: number;
    page_size?: number;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.agent_id) searchParams.set("agent_id", params.agent_id);
    if (params?.page) searchParams.set("page", String(params.page));
    if (params?.page_size) searchParams.set("page_size", String(params.page_size));
    const qs = searchParams.toString();
    return request<PaginatedResponse<Conversation>>(`/conversations${qs ? `?${qs}` : ""}`);
  },

  getConversation: (id: string) => request<Conversation>(`/conversations/${id}`),

  deleteConversation: (id: string) =>
    request<void>(`/conversations/${id}`, { method: "DELETE" }),

  getMessages: (conversationId: string) =>
    request<Message[]>(`/conversations/${conversationId}/messages`),
};

export type { Agent, Conversation, Message, PaginatedResponse };
