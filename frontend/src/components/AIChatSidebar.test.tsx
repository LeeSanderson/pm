import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AIChatSidebar } from "@/components/AIChatSidebar";

describe("AIChatSidebar", () => {
  it("shows the loading state and renders the assistant reply", async () => {
    let resolveRequest: ((value: {
      assistantMessage: string;
      appliedOperations: Array<{ type: string }>;
      model: string;
    }) => void) | null = null;

    const onSubmit = vi.fn(
      () =>
        new Promise<{
          assistantMessage: string;
          appliedOperations: Array<{ type: string }>;
          model: string;
        }>((resolve) => {
          resolveRequest = resolve;
        })
    );

    render(<AIChatSidebar onSubmit={onSubmit} />);

    await userEvent.type(
      screen.getByLabelText(/ask the assistant/i),
      "Move the roadmap card into Review."
    );
    await userEvent.click(screen.getByRole("button", { name: /^send$/i }));

    expect(onSubmit).toHaveBeenCalledWith("Move the roadmap card into Review.");
    expect(await screen.findByText("Reviewing the board and preparing a response.")).toBeInTheDocument();

    resolveRequest?.({
      assistantMessage: "I moved the roadmap card into Review.",
      appliedOperations: [{ type: "move_card" }],
      model: "dummy/openrouter-chat",
    });

    expect(
      await screen.findByText("I moved the roadmap card into Review.")
    ).toBeInTheDocument();
    expect(screen.getByText(/1 board change applied/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /^send$/i })).toHaveTextContent("Send");
    });
  });

  it("shows an error when the request fails", async () => {
    const onSubmit = vi.fn(async () => {
      throw new Error("AI route failed");
    });

    render(<AIChatSidebar onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText(/ask the assistant/i), "No-op");
    await userEvent.click(screen.getByRole("button", { name: /^send$/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("AI route failed");
    expect(screen.getByText("No-op")).toBeInTheDocument();
  });
});