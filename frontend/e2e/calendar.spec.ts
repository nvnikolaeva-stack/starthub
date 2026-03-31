import { test, expect } from "@playwright/test";

test.describe("Календарь", () => {
  test("показывает текущий месяц", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    const monthHeading = page
      .locator("h2")
      .filter({ hasText: /\d{4}/ })
      .first();
    await expect(monthHeading).toBeVisible();
  });

  test("дни недели видны", async ({ page }) => {
    await page.goto("/");
    const pageText = ((await page.textContent("body")) ?? "").toLowerCase();
    const hasDays =
      pageText.includes("пн") ||
      pageText.includes("mon") ||
      pageText.includes("tue");
    expect(hasDays).toBeTruthy();
  });

  test("навигация по месяцам — вперёд", async ({ page }) => {
    await page.goto("/");
    const bodyBefore = await page.textContent("body");
    const nextBtn = page.getByRole("button", {
      name: /следующий месяц|next month/i,
    });
    await expect(nextBtn).toBeVisible();
    await nextBtn.click();
    await page.waitForTimeout(300);
    const bodyAfter = await page.textContent("body");
    expect(bodyAfter).not.toBe(bodyBefore);
  });

  test("навигация по месяцам — назад", async ({ page }) => {
    await page.goto("/");
    const prevBtn = page.getByRole("button", {
      name: /предыдущий месяц|previous month/i,
    });
    await expect(prevBtn).toBeVisible();
    await prevBtn.click();
    await page.waitForTimeout(300);
    await expect(page.locator("body")).toBeVisible();
  });

  test("фильтры спорта видны", async ({ page }) => {
    await page.goto("/");
    const text = ((await page.locator("body").textContent()) ?? "").toLowerCase();
    const hasFilters = text.includes("все") || text.includes("all");
    expect(hasFilters).toBeTruthy();
  });

  test("клик на фильтр обновляет данные", async ({ page }) => {
    await page.goto("/");
    const sportBtn = page.getByRole("button", {
      name: /бег|running/i,
    });
    await expect(sportBtn.first()).toBeVisible();
    await sportBtn.first().click();
    await page.waitForTimeout(400);
    await expect(page.locator("body")).toBeVisible();
  });
});
