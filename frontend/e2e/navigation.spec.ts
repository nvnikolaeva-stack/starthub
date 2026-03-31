import { test, expect } from "@playwright/test";

test.describe("Навигация", () => {
  test("главная страница загружается", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByText(/Календарь стартов|Event calendar|#алкардио|#alkardio/i)
    ).toBeVisible();
  });

  test("навбар содержит все ссылки", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");
    const header = page.locator("header");
    await expect(header).toBeVisible();
    await expect(
      header.getByRole("link", { name: /Календарь|Calendar/i })
    ).toBeVisible();
    await expect(
      header.getByRole("link", { name: /Добавить старт|Add event/i })
    ).toBeVisible();
    await expect(
      header.getByRole("link", { name: /Статистика|Statistics/i })
    ).toBeVisible();
  });

  test("переход на /add", async ({ page }) => {
    await page.goto("/add", { waitUntil: "domcontentloaded" });
    await expect(page).toHaveURL(/\/add$/);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.locator("select#sport")).toBeVisible({ timeout: 15_000 });
  });

  test("переход на /stats", async ({ page }) => {
    await page.goto("/stats");
    await expect(page).toHaveURL(/\/stats$/);
    await expect(
      page.getByRole("heading", { level: 1 }).first()
    ).toBeVisible();
  });

  test("404 — несуществующая страница", async ({ page }) => {
    const response = await page.goto("/nonexistent-page-12345", {
      waitUntil: "domcontentloaded",
    });
    expect(response?.status()).toBe(404);
    await expect(page.locator("body")).toBeVisible();
  });
});
