"use client";

import { useEffect, useRef, useState } from "react";
import type { AIChatOperation } from "@/lib/boardApi";

export type AIChatSubmitResult = {
  assistantMessage: string;
  appliedOperations: AIChatOperation[];
  model: string;
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  meta?: string;
};

type AIChatSidebarProps = {
  onSubmit: (message: string) => Promise<AIChatSubmitResult>;
  disabled?: boolean;
};

const createMessageId = () =>
  `msg-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;

const getErrorMessage = (error: unknown) => {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  return "Unable to send the request.";
};

const getOperationSummary = (result: AIChatSubmitResult) => {
  const changeCount = result.appliedOperations.length;
  const changeLabel =
    changeCount === 0
      ? "No board changes"
      : `${changeCount} board ${changeCount === 1 ? "change" : "changes"} applied`;

  return `${changeLabel} · ${result.model}`;
};

export const AIChatSidebar = ({ onSubmit, disabled = false }: AIChatSidebarProps) => {
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const bottomElement = bottomRef.current;
    if (bottomElement && typeof bottomElement.scrollIntoView === "function") {
      bottomElement.scrollIntoView({ block: "end" });
    }
  }, [messages, isSubmitting]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const nextMessage = draft.trim();
    if (!nextMessage || disabled || isSubmitting) {
      return;
    }

    setDraft("");
    setErrorMessage(null);
    setIsSubmitting(true);
    setMessages((currentMessages) => [
      ...currentMessages,
      { id: createMessageId(), role: "user", content: nextMessage },
    ]);

    try {
      const result = await onSubmit(nextMessage);
      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: createMessageId(),
          role: "assistant",
          content: result.assistantMessage,
          meta: getOperationSummary(result),
        },
      ]);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  const isSendDisabled = disabled || isSubmitting || !draft.trim();

  return (
    <aside
      data-testid="ai-sidebar"
      className="rounded-[32px] border border-[var(--stroke)] bg-white/85 p-6 shadow-[var(--shadow)] backdrop-blur xl:sticky xl:top-8"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.32em] text-[var(--gray-text)]">
            AI sidebar
          </p>
          <h2 className="mt-3 font-display text-2xl font-semibold text-[var(--navy-dark)]">
            Shape the board by chat
          </h2>
        </div>
        <div className="rounded-full border border-[color:rgba(236,173,10,0.3)] bg-[color:rgba(236,173,10,0.12)] px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--navy-dark)]">
          MVP
        </div>
      </div>

      <p className="mt-4 text-sm leading-6 text-[var(--gray-text)]">
        Ask the assistant to create, move, rename, update, or delete cards. The
        board refreshes from the backend response after each reply.
      </p>

      <div className="mt-6 rounded-[28px] border border-[var(--stroke)] bg-[linear-gradient(180deg,_rgba(32,157,215,0.08)_0%,_rgba(255,255,255,0.94)_32%,_rgba(255,255,255,1)_100%)] p-4">
        <div className="flex items-center justify-between gap-3 border-b border-[var(--stroke)] pb-3">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
            Conversation
          </p>
          <p className="text-xs font-medium text-[var(--gray-text)]">
            {isSubmitting ? "Thinking..." : "Ready"}
          </p>
        </div>

        <div className="mt-4 flex max-h-[420px] min-h-[300px] flex-col gap-3 overflow-y-auto pr-1">
          {messages.length === 0 ? (
            <div className="rounded-[24px] border border-dashed border-[var(--stroke)] bg-white/80 px-4 py-5 text-sm leading-6 text-[var(--gray-text)]">
              Try prompts like “Move the roadmap card into Review” or “Add a
              backlog card for stakeholder prep.”
            </div>
          ) : null}

          {messages.map((message) => (
            <div
              key={message.id}
              data-testid={`chat-message-${message.role}`}
              className={
                message.role === "user"
                  ? "ml-auto max-w-[88%] rounded-[22px] rounded-br-md bg-[var(--navy-dark)] px-4 py-3 text-sm leading-6 text-white"
                  : "max-w-[92%] rounded-[22px] rounded-bl-md border border-[var(--stroke)] bg-white px-4 py-3 text-sm leading-6 text-[var(--navy-dark)]"
              }
            >
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] opacity-70">
                {message.role === "user" ? "You" : "Assistant"}
              </p>
              <p className="mt-2 whitespace-pre-wrap">{message.content}</p>
              {message.meta ? (
                <p className="mt-3 text-[11px] font-medium uppercase tracking-[0.12em] text-[var(--gray-text)]">
                  {message.meta}
                </p>
              ) : null}
            </div>
          ))}

          {isSubmitting ? (
            <div className="max-w-[92%] rounded-[22px] rounded-bl-md border border-[var(--stroke)] bg-white px-4 py-3 text-sm text-[var(--gray-text)]">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--gray-text)]">
                Assistant
              </p>
              <p className="mt-2">Reviewing the board and preparing a response.</p>
            </div>
          ) : null}
          <div ref={bottomRef} />
        </div>
      </div>

      {errorMessage ? (
        <div
          role="alert"
          className="mt-4 rounded-2xl border border-[color:rgba(117,57,145,0.2)] bg-[color:rgba(117,57,145,0.08)] px-4 py-3 text-sm font-medium text-[var(--navy-dark)]"
        >
          {errorMessage}
        </div>
      ) : null}

      <form className="mt-5" onSubmit={handleSubmit}>
        <label htmlFor="ai-chat-message" className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--gray-text)]">
          Ask the assistant
        </label>
        <textarea
          id="ai-chat-message"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          rows={4}
          placeholder="Describe the board change you want."
          disabled={disabled || isSubmitting}
          className="mt-3 w-full rounded-[24px] border border-[var(--stroke)] bg-[var(--surface)] px-4 py-4 text-sm leading-6 text-[var(--navy-dark)] outline-none transition placeholder:text-[var(--gray-text)] focus:border-[var(--primary-blue)] disabled:cursor-not-allowed disabled:opacity-70"
        />
        <div className="mt-4 flex items-center justify-between gap-4">
          <p className="text-xs leading-5 text-[var(--gray-text)]">
            Chat history stays in backend memory for this session only.
          </p>
          <button
            type="submit"
            disabled={isSendDisabled}
            className="rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-xs font-semibold uppercase tracking-[0.16em] text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "Sending..." : "Send"}
          </button>
        </div>
      </form>
    </aside>
  );
};