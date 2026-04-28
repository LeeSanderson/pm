import { expect, test } from "@playwright/test";

const createBoardSnapshot = () => ({
  columns: [
    { id: "col-backlog", title: "Backlog", cardIds: ["card-2", "card-ai-1"] },
    { id: "col-discovery", title: "Discovery", cardIds: ["card-3"] },
    { id: "col-progress", title: "In Progress", cardIds: ["card-4", "card-5"] },
    { id: "col-review", title: "Review", cardIds: ["card-1", "card-6"] },
    { id: "col-done", title: "Done", cardIds: ["card-7", "card-8"] },
  ],
  cards: {
    "card-1": {
      id: "card-1",
      title: "Align roadmap themes",
      details: "Moved into review with AI guidance.",
    },
    "card-2": {
      id: "card-2",
      title: "Gather customer signals",
      details: "Review support tags, sales notes, and churn feedback.",
    },
    "card-3": {
      id: "card-3",
      title: "Prototype analytics view",
      details: "Sketch initial dashboard layout and key drill-downs.",
    },
    "card-4": {
      id: "card-4",
      title: "Refine status language",
      details: "Standardize column labels and tone across the board.",
    },
    "card-5": {
      id: "card-5",
      title: "Design card layout",
      details: "Add hierarchy and spacing for scanning dense lists.",
    },
    "card-6": {
      id: "card-6",
      title: "QA micro-interactions",
      details: "Verify hover, focus, and loading states.",
    },
    "card-7": {
      id: "card-7",
      title: "Ship marketing page",
      details: "Final copy approved and asset pack delivered.",
    },
    "card-8": {
      id: "card-8",
      title: "Close onboarding sprint",
      details: "Document release notes and share internally.",
    },
    "card-ai-1": {
      id: "card-ai-1",
      title: "Prep roadmap summary",
      details: "Share the updated review notes with stakeholders.",
    },
  },
});

const resetBoard = async (page: import("@playwright/test").Page) => {
  const response = await page.request.post("/api/test/reset-board");
  expect(response.ok()).toBeTruthy();
};

const login = async (page: import("@playwright/test").Page) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /sign in to continue/i })
  ).toBeVisible();
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /^sign in$/i }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
};

test.beforeEach(async ({ page }) => {
  await resetBoard(page);
});

test("requires login before showing the board", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /sign in to continue/i })
  ).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(0);
});

test("shows an error for invalid credentials", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("wrong");
  await page.getByRole("button", { name: /^sign in$/i }).click();

  await expect(page.locator("form [role='alert']")).toContainText(
    "Invalid credentials"
  );
  await expect(
    page.getByRole("heading", { name: /sign in to continue/i })
  ).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(0);
});

test("signs in and loads the kanban board", async ({ page }) => {
  await login(page);
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await login(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();

  await page.reload();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await login(page);
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();

  await page.reload();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("persists the session across reload and supports logout", async ({ page }) => {
  await login(page);
  await page.reload();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await page.getByRole("button", { name: /log out/i }).click();
  await expect(
    page.getByRole("heading", { name: /sign in to continue/i })
  ).toBeVisible();
});

test("sends a chat prompt and refreshes the board from the AI response", async ({ page }) => {
  await page.route("**/api/ai/chat", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        assistantMessage:
          "I moved the roadmap card into Review and added a prep summary card.",
        appliedOperations: [{ type: "move_card" }, { type: "create_card" }],
        board: createBoardSnapshot(),
        model: "dummy/openrouter-chat",
      }),
    });
  });

  await login(page);
  await page.getByLabel("Ask the assistant").fill(
    "Move the roadmap card into review and add a prep summary task."
  );
  await page.getByRole("button", { name: /^send$/i }).click();

  await expect(
    page.getByText("I moved the roadmap card into Review and added a prep summary card.")
  ).toBeVisible();
  await expect(page.getByText("Prep roadmap summary")).toBeVisible();
  await expect(page.getByText(/2 board changes applied/i)).toBeVisible();
});

test("renders an AI no-op response without changing the board", async ({ page }) => {
  await page.route("**/api/ai/chat", async (route) => {
    const boardResponse = await page.request.get("/api/board");
    const board = await boardResponse.json();

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        assistantMessage: "No board changes needed.",
        appliedOperations: [],
        board,
        model: "dummy/openrouter-chat",
      }),
    });
  });

  await login(page);
  await page.getByLabel("Ask the assistant").fill("No board changes needed.");
  await page.getByRole("button", { name: /^send$/i }).click();

  await expect(
    page.getByTestId("chat-message-assistant").getByText("No board changes needed.")
  ).toBeVisible();
  await expect(
    page.getByTestId("chat-message-assistant").getByText(/^No board changes ·/i)
  ).toBeVisible();
  await expect(page.getByTestId("card-card-1")).toBeVisible();
  await expect(page.getByText("Prep roadmap summary")).toHaveCount(0);
});
