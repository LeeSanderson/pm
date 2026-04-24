import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanApp } from "@/components/KanbanApp";

const jsonResponse = (body: unknown, status = 200) =>
  ({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  }) as Response;

describe("KanbanApp", () => {
  const fetchMock = vi.fn<typeof fetch>();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("shows the login screen when the session is missing", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ detail: "Not authenticated" }, 401)
    );

    render(<KanbanApp />);

    expect(
      await screen.findByRole("heading", { name: /sign in to continue/i })
    ).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Kanban Studio" })).not.toBeInTheDocument();
  });

  it("signs in successfully and renders the board", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ detail: "Not authenticated" }, 401))
      .mockResolvedValueOnce(jsonResponse({ username: "user" }));

    render(<KanbanApp />);

    await screen.findByRole("heading", { name: /sign in to continue/i });
    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(
      await screen.findByRole("heading", { name: "Kanban Studio" })
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /log out/i })).toBeInTheDocument();
  });

  it("shows an error for invalid credentials", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ detail: "Not authenticated" }, 401))
      .mockResolvedValueOnce(jsonResponse({ detail: "Invalid credentials" }, 401));

    render(<KanbanApp />);

    await screen.findByRole("heading", { name: /sign in to continue/i });
    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "wrong" );
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid credentials");
    expect(screen.getByRole("heading", { name: /sign in to continue/i })).toBeInTheDocument();
  });

  it("logs out and returns to the login screen", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ username: "user" }))
      .mockResolvedValueOnce({ ok: true, status: 204, json: async () => ({}) } as Response);

    render(<KanbanApp />);

    await screen.findByRole("heading", { name: "Kanban Studio" });
    await userEvent.click(screen.getByRole("button", { name: /log out/i }));

    expect(
      await screen.findByRole("heading", { name: /sign in to continue/i })
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/auth/logout",
        expect.objectContaining({ method: "POST" })
      );
    });
  });
});