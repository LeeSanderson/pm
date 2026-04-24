import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData, type BoardData } from "@/lib/kanban";

const jsonResponse = (body: unknown, status = 200) =>
  ({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  }) as Response;

const cloneBoard = (): BoardData =>
  JSON.parse(JSON.stringify(initialData)) as BoardData;

const createBoardApiMock = () => {
  let board = cloneBoard();
  let nextCardId = 100;

  const currentBoard = () => JSON.parse(JSON.stringify(board)) as BoardData;

  return vi.fn<typeof fetch>(async (input, init) => {
    const url = typeof input === "string" ? input : input.toString();
    const method = init?.method ?? "GET";

    if (url === "/api/board" && method === "GET") {
      return jsonResponse(currentBoard());
    }

    const renameMatch = url.match(/^\/api\/board\/columns\/([^/]+)$/);
    if (renameMatch && method === "PATCH") {
      const payload = JSON.parse(String(init?.body ?? "{}")) as { title: string };
      board = {
        ...board,
        columns: board.columns.map((column) =>
          column.id === renameMatch[1]
            ? { ...column, title: payload.title }
            : column
        ),
      };
      return jsonResponse(currentBoard());
    }

    const addMatch = url.match(/^\/api\/board\/columns\/([^/]+)\/cards$/);
    if (addMatch && method === "POST") {
      const payload = JSON.parse(String(init?.body ?? "{}")) as {
        title: string;
        details: string;
      };
      const cardId = `card-test-${nextCardId++}`;
      board = {
        ...board,
        cards: {
          ...board.cards,
          [cardId]: {
            id: cardId,
            title: payload.title,
            details: payload.details || "No details yet.",
          },
        },
        columns: board.columns.map((column) =>
          column.id === addMatch[1]
            ? { ...column, cardIds: [...column.cardIds, cardId] }
            : column
        ),
      };
      return jsonResponse(currentBoard());
    }

    const deleteMatch = url.match(/^\/api\/board\/columns\/([^/]+)\/cards\/([^/]+)$/);
    if (deleteMatch && method === "DELETE") {
      const [, columnId, cardId] = deleteMatch;
      board = {
        ...board,
        cards: Object.fromEntries(
          Object.entries(board.cards).filter(([id]) => id !== cardId)
        ),
        columns: board.columns.map((column) =>
          column.id === columnId
            ? {
                ...column,
                cardIds: column.cardIds.filter((id) => id !== cardId),
              }
            : column
        ),
      };
      return jsonResponse(currentBoard());
    }

    return jsonResponse({ detail: `Unhandled request: ${method} ${url}` }, 500);
  });
};

const getFirstColumn = async () => (await screen.findAllByTestId(/column-/i))[0];

describe("KanbanBoard", () => {
  const fetchMock = vi.fn<typeof fetch>();

  beforeEach(() => {
    fetchMock.mockImplementation(createBoardApiMock());
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("renders five columns", () => {
    render(<KanbanBoard />);
    return expect(screen.findAllByTestId(/column-/i)).resolves.toHaveLength(5);
  });

  it("renames a column", async () => {
    render(<KanbanBoard />);
    const column = await getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    await userEvent.tab();

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/board/columns/col-backlog",
        expect.objectContaining({ method: "PATCH" })
      );
    });

    expect(input).toHaveValue("New Name");
  });

  it("adds and removes a card", async () => {
    render(<KanbanBoard />);
    const column = await getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/board/columns/col-backlog/cards",
        expect.objectContaining({ method: "POST" })
      );
    });

    expect(await screen.findByText("New card")).toBeInTheDocument();

    const updatedColumn = screen.getByTestId("column-col-backlog");
    const deleteButton = within(updatedColumn).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringMatching(/^\/api\/board\/columns\/col-backlog\/cards\/card-test-/),
        expect.objectContaining({ method: "DELETE" })
      );
    });

    expect(screen.queryByText("New card")).not.toBeInTheDocument();
  });
});
