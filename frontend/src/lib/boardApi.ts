import type { BoardData } from "@/lib/kanban";

type ErrorPayload = {
  detail?: string;
};

export class BoardApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "BoardApiError";
    this.status = status;
  }
}

const getErrorMessage = async (response: Response, fallback: string) => {
  try {
    const payload = (await response.json()) as ErrorPayload;
    return payload.detail ?? fallback;
  } catch {
    return fallback;
  }
};

const requestBoard = async (
  input: string,
  init: RequestInit | undefined,
  fallbackMessage: string
): Promise<BoardData> => {
  const response = await fetch(input, {
    credentials: "same-origin",
    ...init,
  });

  if (!response.ok) {
    throw new BoardApiError(
      response.status,
      await getErrorMessage(response, fallbackMessage)
    );
  }

  return (await response.json()) as BoardData;
};

export const fetchBoard = () => requestBoard("/api/board", undefined, "Unable to load board.");

export const renameColumn = (columnId: string, title: string) =>
  requestBoard(
    `/api/board/columns/${columnId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ title }),
    },
    "Unable to rename column."
  );

export const addCard = (columnId: string, title: string, details: string) =>
  requestBoard(
    `/api/board/columns/${columnId}/cards`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ title, details }),
    },
    "Unable to add card."
  );

export const deleteCard = (columnId: string, cardId: string) =>
  requestBoard(
    `/api/board/columns/${columnId}/cards/${cardId}`,
    {
      method: "DELETE",
    },
    "Unable to delete card."
  );

export const moveCard = (cardId: string, columnId: string, position: number) =>
  requestBoard(
    `/api/board/cards/${cardId}/move`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ column_id: columnId, position }),
    },
    "Unable to move card."
  );