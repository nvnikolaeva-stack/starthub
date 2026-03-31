import { test, expect } from "@playwright/test";

function tomorrowIso(): string {
  const t = new Date();
  t.setDate(t.getDate() + 1);
  return t.toISOString().slice(0, 10);
}

test.describe("Форма добавления старта", () => {
  test("форма загружается", async ({ page }) => {
    await page.goto("/add", { waitUntil: "domcontentloaded" });
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.locator("select#sport")).toBeVisible({ timeout: 15_000 });
    await expect(page.locator('input#title')).toBeVisible();
  });

  test("создание старта — полный флоу", async ({ page }) => {
    const distReady = page.waitForResponse(
      (r) =>
        r.url().includes("/api/v1/distances/running") && r.status() === 200,
      { timeout: 25_000 }
    );
    await page.goto("/add", { waitUntil: "domcontentloaded" });
    await distReady;

    const raceName = `Playwright E2E ${Date.now()}`;
    await page.locator('input#title').fill(raceName);

    await page.locator('input#ds[type="date"]').fill(tomorrowIso());

    await page.locator('input#loc').fill("Berlin");

    const chip = page
      .locator("form button.rounded-full.border-2.border-slate-300")
      .first();
    await chip.waitFor({ state: "visible", timeout: 20_000 });
    await chip.click();

    await page.locator("input#author-name").scrollIntoViewIfNeeded();
    await page.locator("input#author-name").fill("E2E Runner");

    const saveBtn = page.getByRole("button", {
      name: /сохранить|save event/i,
    });
    await saveBtn.click();

    await expect(page).toHaveURL(/\/event\/[a-zA-Z0-9-]+/, {
      timeout: 25_000,
    });
    await expect(page.getByText(raceName).first()).toBeVisible({
      timeout: 15_000,
    });
  });

  test("валидация — пустая форма", async ({ page }) => {
    await page.goto("/add", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(300);

    const saveBtn = page.getByRole("button", {
      name: /сохранить|save event/i,
    });
    await saveBtn.click();
    await page.waitForTimeout(400);

    await expect(page).toHaveURL(/\/add$/);
  });
});
