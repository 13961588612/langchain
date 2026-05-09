"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";

export default function NewAgentPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    name: "",
    description: "",
    system_prompt: "",
    model_provider: "openai",
    model_name: "gpt-4o",
    soul_config: "",
    profile_config: "",
  });

  function updateField(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) {
      setError("Agent name is required");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const agent = await api.createAgent(form);
      router.push(`/agents/${agent.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create agent");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-6">
        <Link href="/" className="text-sm text-gray-500 hover:text-gray-700">
          &larr; Back
        </Link>
        <h1 className="mt-2 text-2xl font-bold text-gray-900">Create Agent</h1>
        <p className="text-sm text-gray-500">
          Configure a new AI agent with custom personality and behavior
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <div className="card p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">
            Basic Information
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name *
              </label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => updateField("name", e.target.value)}
                placeholder="My Agent"
                className="input-field"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={form.description}
                onChange={(e) => updateField("description", e.target.value)}
                placeholder="What does this agent do?"
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
                placeholder="You are a helpful assistant..."
                rows={5}
                className="input-field font-mono text-xs"
              />
            </div>
          </div>
        </div>

        {/* Model Configuration */}
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
                placeholder="gpt-4o"
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
                placeholder={`tone: friendly\nstyle: concise\nvalues:\n  - helpfulness\n  - accuracy`}
                rows={4}
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
                placeholder={`response_length: moderate\ntool_usage: proactive\ninitiative: medium`}
                rows={4}
                className="input-field font-mono text-xs"
              />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3">
          <Link href="/" className="btn-secondary">
            Cancel
          </Link>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? "Creating..." : "Create Agent"}
          </button>
        </div>
      </form>
    </div>
  );
}
