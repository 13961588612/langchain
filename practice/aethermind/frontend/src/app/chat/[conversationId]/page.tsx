"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ChatInterface } from "@/components/ChatInterface";
import { api, Conversation, Message } from "@/lib/api";

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
  const conversationId = params.conversationId as string;

  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [streamingContent, setStreamingContent] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);

  useEffect(() => {
    loadConversation();
  }, [conversationId]);

  async function loadConversation() {
    try {
      const conv = await api.getConversation(conversationId);
      setConversation(conv);
      const msgs = await api.getMessages(conversationId);
      setMessages(msgs);
    } catch (err) {
      console.error("Failed to load conversation:", err);
    } finally {
      setLoading(false);
    }
  }

  const handleSendMessage = useCallback(
    async (message: string) => {
      if (!conversation) return;

      const userMsg: Message = {
        id: `user-${Date.now()}`,
        conversation_id: conversationId,
        role: "user",
        content: message,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);

      setIsStreaming(true);
      setStreamingContent("");

      try {
        const res = await fetch(`/api/conversations/${conversationId}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message }),
        });

        const reader = res.body?.getReader();
        if (!reader) {
          throw new Error("No response body");
        }

        const decoder = new TextDecoder();
        let buffer = "";
        let fullContent = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || !trimmed.startsWith("data: ")) continue;

            try {
              const data = JSON.parse(trimmed.slice(6));
              const event = data.event;

              if (event === "token") {
                fullContent += data.content;
                setStreamingContent(fullContent);
              } else if (event === "tool_call") {
                setStreamingContent(
                  (prev) =>
                    prev + `\n\n> 🔧 ${data.content}\n\n`
                );
              } else if (event === "tool_result") {
                // Tool result - could show inline
              } else if (event === "done") {
                const assistantMsg: Message = {
                  id: `assistant-${Date.now()}`,
                  conversation_id: conversationId,
                  role: "assistant",
                  content: fullContent || data.content,
                  created_at: new Date().toISOString(),
                };
                setMessages((prev) => [...prev, assistantMsg]);
                setStreamingContent("");
              } else if (event === "error") {
                console.error("Stream error:", data.content);
                setStreamingContent(`Error: ${data.content}`);
              }
            } catch {
              // Skip malformed JSON
            }
          }
        }
      } catch (err) {
        console.error("Chat error:", err);
        setStreamingContent(
          `Error: ${err instanceof Error ? err.message : "Connection failed"}`
        );
      } finally {
        setIsStreaming(false);
      }
    },
    [conversationId, conversation]
  );

  if (loading) {
    return (
      <div className="text-center py-16 text-gray-400">
        Loading conversation...
      </div>
    );
  }

  if (!conversation) {
    return (
      <div className="text-center py-16">
        <h2 className="text-lg font-medium text-gray-900">
          Conversation not found
        </h2>
        <Link href="/" className="btn-secondary mt-4 inline-flex">
          Back to Home
        </Link>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div>
          <Link href="/" className="text-sm text-gray-500 hover:text-gray-700">
            &larr; Home
          </Link>
          <h1 className="text-lg font-semibold text-gray-900">
            {conversation.title || "Chat"}
          </h1>
        </div>
        <div className="text-xs text-gray-400">
          Thread: {conversation.thread_id.slice(0, 8)}...
        </div>
      </div>

      {/* Chat */}
      <div className="card overflow-hidden">
        <ChatInterface
          conversationId={conversationId}
          initialMessages={messages.map((m) => ({
            role: m.role as "user" | "assistant",
            content: m.content,
            id: m.id,
          }))}
          onSendMessage={handleSendMessage}
          streamingContent={streamingContent}
          isStreaming={isStreaming}
        />
      </div>
    </div>
  );
}
