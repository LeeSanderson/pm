"use client";

import { useEffect, useEffectEvent, useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { AIChatSidebar, type AIChatSubmitResult } from "@/components/AIChatSidebar";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import {
  addCard as addCardRequest,
  BoardApiError,
  chatWithAI,
  deleteCard as deleteCardRequest,
  fetchBoard,
  moveCard as moveCardRequest,
  renameColumn as renameColumnRequest,
} from "@/lib/boardApi";
import { moveCard, type BoardData, type Column } from "@/lib/kanban";

type BoardStatus = "loading" | "ready" | "error";

type KanbanBoardProps = {
  username?: string;
  onLogout?: () => void;
  isLoggingOut?: boolean;
  onSessionExpired?: () => void;
};

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
};

const findCardLocation = (columns: Column[], cardId: string) => {
  const column = columns.find((currentColumn) =>
    currentColumn.cardIds.includes(cardId)
  );

  if (!column) {
    return null;
  }

  return {
    columnId: column.id,
    position: column.cardIds.indexOf(cardId),
  };
};

export const KanbanBoard = ({
  username,
  onLogout,
  isLoggingOut = false,
  onSessionExpired,
}: KanbanBoardProps) => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [boardStatus, setBoardStatus] = useState<BoardStatus>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isAiPending, setIsAiPending] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);
  const isBusy = isSaving || isAiPending;

  const handleSessionExpired = useEffectEvent(() => {
    onSessionExpired?.();
  });

  useEffect(() => {
    let isMounted = true;

    const loadBoard = async () => {
      setBoardStatus("loading");
      setErrorMessage(null);

      try {
        const nextBoard = await fetchBoard();

        if (!isMounted) {
          return;
        }

        setBoard(nextBoard);
        setBoardStatus("ready");
      } catch (error) {
        if (!isMounted) {
          return;
        }

        if (error instanceof BoardApiError && error.status === 401) {
          handleSessionExpired();
          return;
        }

        setBoard(null);
        setBoardStatus("error");
        setErrorMessage(getErrorMessage(error, "Unable to load board."));
      }
    };

    void loadBoard();

    return () => {
      isMounted = false;
    };
  }, [reloadToken]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const cardsById = useMemo(() => board?.cards ?? {}, [board]);

  const handleDragStart = (event: DragStartEvent) => {
    if (isBusy) {
      return;
    }

    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!board || isBusy || !over || active.id === over.id) {
      return;
    }

    const nextColumns = moveCard(
      board.columns,
      active.id as string,
      over.id as string
    );
    if (nextColumns === board.columns) {
      return;
    }

    const destination = findCardLocation(nextColumns, active.id as string);
    if (!destination) {
      return;
    }

    const previousBoard = board;
    setBoard({ ...board, columns: nextColumns });
    setErrorMessage(null);
    setIsSaving(true);

    try {
      setBoard(
        await moveCardRequest(
          active.id as string,
          destination.columnId,
          destination.position
        )
      );
    } catch (error) {
      setBoard(previousBoard);

      if (error instanceof BoardApiError && error.status === 401) {
        handleSessionExpired();
        return;
      }

      setErrorMessage(getErrorMessage(error, "Unable to move card."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleRenameColumn = async (columnId: string, title: string) => {
    if (!board || isBusy) {
      return;
    }

    const normalizedTitle = title.trim();
    const column = board.columns.find((currentColumn) => currentColumn.id === columnId);
    if (!column || normalizedTitle === column.title) {
      return;
    }

    const previousBoard = board;
    setBoard({
      ...board,
      columns: board.columns.map((currentColumn) =>
        currentColumn.id === columnId
          ? { ...currentColumn, title: normalizedTitle }
          : currentColumn
      ),
    });
    setErrorMessage(null);
    setIsSaving(true);

    try {
      setBoard(await renameColumnRequest(columnId, normalizedTitle));
    } catch (error) {
      setBoard(previousBoard);

      if (error instanceof BoardApiError && error.status === 401) {
        handleSessionExpired();
        return;
      }

      setErrorMessage(getErrorMessage(error, "Unable to rename column."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddCard = async (columnId: string, title: string, details: string) => {
    if (!board || isBusy) {
      return;
    }

    setErrorMessage(null);
    setIsSaving(true);

    try {
      setBoard(await addCardRequest(columnId, title, details));
    } catch (error) {
      if (error instanceof BoardApiError && error.status === 401) {
        handleSessionExpired();
        return;
      }

      setErrorMessage(getErrorMessage(error, "Unable to add card."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteCard = async (columnId: string, cardId: string) => {
    if (!board || isBusy) {
      return;
    }

    setErrorMessage(null);
    setIsSaving(true);

    try {
      setBoard(await deleteCardRequest(columnId, cardId));
    } catch (error) {
      if (error instanceof BoardApiError && error.status === 401) {
        handleSessionExpired();
        return;
      }

      setErrorMessage(getErrorMessage(error, "Unable to delete card."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleAIChat = async (message: string): Promise<AIChatSubmitResult> => {
    if (!board || isBusy) {
      throw new Error("Please wait for current board changes to finish.");
    }

    setIsAiPending(true);

    try {
      const response = await chatWithAI(message);
      setBoard(response.board);
      return {
        assistantMessage: response.assistantMessage,
        appliedOperations: response.appliedOperations,
        model: response.model,
      };
    } catch (error) {
      if (error instanceof BoardApiError && error.status === 401) {
        handleSessionExpired();
        throw new Error("Your session expired. Sign in again.");
      }

      throw error;
    } finally {
      setIsAiPending(false);
    }
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  if (boardStatus === "loading") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-6 py-10">
        <div className="rounded-[28px] border border-[var(--stroke)] bg-white/90 px-8 py-10 text-center shadow-[var(--shadow)]">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
            Loading board
          </p>
          <p className="mt-4 text-sm text-[var(--gray-text)]">
            Pulling the latest saved board from the backend.
          </p>
        </div>
      </main>
    );
  }

  if (boardStatus === "error" || !board) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-6 py-10">
        <div className="max-w-md rounded-[28px] border border-[var(--stroke)] bg-white/90 px-8 py-10 text-center shadow-[var(--shadow)]">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
            Board unavailable
          </p>
          <p className="mt-4 text-sm leading-6 text-[var(--gray-text)]">
            {errorMessage ?? "Unable to load board."}
          </p>
          <button
            type="button"
            onClick={() => setReloadToken((current) => current + 1)}
            className="mt-6 rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-xs font-semibold uppercase tracking-[0.15em] text-white transition hover:brightness-110"
          >
            Retry
          </button>
        </div>
      </main>
    );
  }

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="flex flex-col gap-3">
              <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                  Focus
                </p>
                <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                  One board. Five columns. Zero clutter.
                </p>
              </div>
              <div className="rounded-2xl border border-[var(--stroke)] bg-white/90 px-5 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                  Sync
                </p>
                <p className="mt-2 text-sm font-semibold text-[var(--navy-dark)]">
                  {isAiPending
                    ? "Applying AI changes..."
                    : isSaving
                      ? "Saving changes..."
                      : "Changes persist automatically."}
                </p>
              </div>
              {onLogout ? (
                <div className="flex items-center justify-between gap-4 rounded-2xl border border-[var(--stroke)] bg-white/90 px-5 py-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                      Session
                    </p>
                    <p className="mt-2 text-sm font-semibold text-[var(--navy-dark)]">
                      Signed in as {username ?? "user"}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={onLogout}
                    disabled={isLoggingOut}
                    className="rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.15em] text-[var(--navy-dark)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)] disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isLoggingOut ? "Logging out..." : "Log out"}
                  </button>
                </div>
              ) : null}
            </div>
          </div>
          {errorMessage ? (
            <div
              role="alert"
              className="rounded-2xl border border-[color:rgba(117,57,145,0.2)] bg-[color:rgba(117,57,145,0.08)] px-4 py-3 text-sm font-medium text-[var(--navy-dark)]"
            >
              {errorMessage}
            </div>
          ) : null}
          <div className="flex flex-wrap items-center gap-4">
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
        </header>

        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
            <div className="overflow-x-auto pb-4">
              <section className="grid min-w-[1120px] gap-6 lg:grid-cols-5">
                {board.columns.map((column) => (
                  <KanbanColumn
                    key={column.id}
                    column={column}
                    cards={column.cardIds.map((cardId) => board.cards[cardId])}
                    onRename={handleRenameColumn}
                    onAddCard={handleAddCard}
                    onDeleteCard={handleDeleteCard}
                  />
                ))}
              </section>
            </div>
            <AIChatSidebar onSubmit={handleAIChat} disabled={isBusy} />
          </div>
          <DragOverlay>
            {activeCard ? (
              <div className="w-[260px]">
                <KanbanCardPreview card={activeCard} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </main>
    </div>
  );
};
