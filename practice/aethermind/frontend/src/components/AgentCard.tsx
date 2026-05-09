"use client";

import Link from "next/link";
import { api, Agent } from "@/lib/api";
import { formatDate } from "@/lib/utils";

interface AgentCardProps {
  agent: Agent;
  onDelete?: () => void;
}

export function AgentCard({ agent, onDelete }: AgentCardProps) {
  async function handleDelete(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm(`Delete agent "${agent.name}"?`)) return;
    try {
      await api.deleteAgent(agent.id);
      onDelete?.();
    } catch (err) {
      console.error("Failed to delete agent:", err);
    }
  }

  async function handleToggle(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    try {
      await api.toggleAgent(agent.id, !agent.is_active);
      onDelete?.();
    } catch (err) {
      console.error("Failed to toggle agent:", err);
    }
  }

  return (
    <Link href={`/agents/${agent.id}`} className="card block p-5 group">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-100 text-primary-700 font-bold text-xs">
            {agent.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h3 className="font-medium text-gray-900 group-hover:text-primary-600 transition-colors">
              {agent.name}
            </h3>
            <p className="text-xs text-gray-400">
              {agent.model_provider}:{agent.model_name}
            </p>
          </div>
        </div>
        <span
          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
            agent.is_active
              ? "bg-green-50 text-green-700 ring-1 ring-inset ring-green-600/20"
              : "bg-gray-50 text-gray-500 ring-1 ring-inset ring-gray-500/10"
          }`}
        >
          {agent.is_active ? "Active" : "Inactive"}
        </span>
      </div>

      {agent.description && (
        <p className="text-sm text-gray-500 line-clamp-2 mb-4">
          {agent.description}
        </p>
      )}

      <div className="flex items-center justify-between text-xs text-gray-400">
        <span>{formatDate(agent.created_at)}</span>
        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={handleToggle}
            className="text-gray-500 hover:text-primary-600"
            title={agent.is_active ? "Deactivate" : "Activate"}
          >
            {agent.is_active ? "Pause" : "Start"}
          </button>
          <button
            onClick={handleDelete}
            className="text-gray-500 hover:text-red-600"
            title="Delete"
          >
            Delete
          </button>
        </div>
      </div>
    </Link>
  );
}
