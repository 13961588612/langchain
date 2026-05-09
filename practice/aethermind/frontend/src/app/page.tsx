"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { AgentCard } from "@/components/AgentCard";
import { api } from "@/lib/api";

interface Agent {
  id: string;
  name: string;
  description?: string;
  model_provider: string;
  model_name: string;
  is_active: boolean;
  created_at: string;
}

export default function HomePage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    loadAgents();
  }, [search]);

  async function loadAgents() {
    setLoading(true);
    try {
      const data = await api.listAgents({ search: search || undefined });
      setAgents(data.items);
    } catch (err) {
      console.error("Failed to load agents:", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      {/* Hero */}
      <div className="mb-10 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
          AetherMind
        </h1>
        <p className="mt-3 text-lg text-gray-500">
          Create, configure, and orchestrate AI agents with ease
        </p>
      </div>

      {/* Search & Actions */}
      <div className="mb-6 flex items-center gap-4">
        <input
          type="text"
          placeholder="Search agents..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field max-w-sm"
        />
        <Link href="/agents/new" className="btn-primary">
          + New Agent
        </Link>
      </div>

      {/* Stats */}
      <div className="mb-8 grid grid-cols-3 gap-4">
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-primary-600">
            {loading ? "..." : agents.length}
          </div>
          <div className="text-xs text-gray-500 mt-1">Total Agents</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-green-600">
            {loading ? "..." : agents.filter((a) => a.is_active).length}
          </div>
          <div className="text-xs text-gray-500 mt-1">Active</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-gray-400">
            {loading ? "..." : agents.filter((a) => !a.is_active).length}
          </div>
          <div className="text-xs text-gray-500 mt-1">Inactive</div>
        </div>
      </div>

      {/* Agent Grid */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading agents...</div>
      ) : agents.length === 0 ? (
        <div className="card py-16 text-center">
          <div className="text-4xl mb-3">🤖</div>
          <h3 className="text-lg font-medium text-gray-900">
            No agents yet
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Create your first agent to get started
          </p>
          <Link href="/agents/new" className="btn-primary mt-4 inline-flex">
            Create Agent
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      )}
    </div>
  );
}
