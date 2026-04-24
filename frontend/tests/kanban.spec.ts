import { expect, test } from "@playwright/test";

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
