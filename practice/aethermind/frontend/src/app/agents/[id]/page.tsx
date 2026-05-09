"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, Agent } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.id as string;

  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [form, setForm] = useState({
    name: "",
    description: "",
    system_prompt: "",
    model_provider: "openai",
    model_name: "gpt-4o",
    soul_config: "",
    profile_config: "",
  });

  useEffect(() => {
    loadAgent();
  }, [agentId]);

  async function loadAgent() {
    try {
      const data = await api.getAgent(agentId);
      setAgent(data);
      setForm({
        name: data.name,
        description: data.description || "",
        system_prompt: data.system_prompt || "",
        model_provider: data.model_provider,
        model_name: data.model_name,
        soul_config: data.soul_config || "",
        profile_config: data.profile_config || "",
      });
    } catch (err) {
      console.error("Failed to load agent:", err);
    } finally {
      setLoading(false);
    }
  }

  function updateField(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setSuccess("");
  }

  async function handleSave() {
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const updated = await api.updateAgent(agentId, form);
      setAgent(updated);
      setSuccess("Agent updated successfully");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete agent "${agent?.name}"?`)) return;
    try {
      await api.deleteAgent(agentId);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete");
    }
  }

  async function handleToggle() {
    if (!agent) return;
    try {
      const updated = await api.toggleAgent(agentId, !agent.is_active);
      setAgent(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to toggle");
    }
  }

  async function startChat() {
    try {
      const conv = await api.createConversation(agentId, `Chat with ${agent?.name}`);
      router.push(`/chat/${conv.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start chat");
    }
  }

  if (loading) {
    return (
      <div className="text-center py-16 text-gray-400">Loading agent...</div>
    );
  }

  if (!agent) {
    return (
      <div className="text-center py-16">
        <h2 className="text-lg font-medium text-gray-900">Agent not found</h2>
        <Link href="/" className="btn-secondary mt-4 inline-flex">
          Back to Home
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link href="/" className="text-sm text-gray-500 hover:text-gray-700">
            &larr; Back
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-gray-900">
            {agent.name}
          </h1>
          <p className="text-sm text-gray-500">{formatDate(agent.created_at)}</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleToggle} className="btn-secondary text-xs">
            {agent.is_active ? "Deactivate" : "Activate"}
          </button>
          <button onClick={startChat} className="btn-primary text-xs">
            Chat
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          {success}
        </div>
      )}

      <div className="space-y-6">
        {/* Basic Info */}
        <div className="card p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">
            Basic Information
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name
              </label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => updateField("name", e.target.value)}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={form.description}
                onChange={(e) => updateField("description", e.target.value)}
                rows={3}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                System Prompt
              </label>
              <textarea
                value={form.system_prompt}
                onChange={(e) => updateField("system_prompt", e.target.value)}
                rows={6}
                className="input-field font-mono text-xs"
              />
            </div>
          </div>
        </div>

        {/* Model Config */}
        <div className="card p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">
            Model Configuration
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Provider
              </label>
              <select
                value={form.model_provider}
                onChange={(e) => updateField("model_provider", e.target.value)}
                className="input-field"
              >
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="google">Google Gemini</option>
                <option value="azure">Azure OpenAI</option>
                <option value="ollama">Ollama (Local)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Model
              </label>
              <input
                type="text"
                value={form.model_name}
                onChange={(e) => updateField("model_name", e.target.value)}
                className="input-field"
              />
            </div>
          </div>
        </div>

        {/* Personality */}
        <div className="card p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">
            Personality & Soul
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Soul Configuration (YAML)
              </label>
              <textarea
                value={form.soul_config}
                onChange={(e) => updateField("soul_config", e.target.value)}
                rows={6}
                className="input-field font-mono text-xs"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Profile Configuration (YAML)
              </label>
              <textarea
                value={form.profile_config}
                onChange={(e) => updateField("profile_config", e.target.value)}
                rows={6}
                className="input-field font-mono text-xs"
              />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between">
          <button onClick={handleDelete} className="btn-danger text-xs">
            Delete Agent
          </button>
          <button
            onClick={handleSave}
            className="btn-primary"
            disabled={saving}
          >
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>
    </div>
  );
}
