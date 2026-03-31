import { test, expect } from "@playwright/test";

test.describe("Страница старта", () => {
  test("карточка старта из списка", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});

    const detailLink = page.getByRole("link", {
      name: /подробнее|details/i,
    });
    test.skip(
      (await detailLink.count()) === 0,
      "В ленте нет стартов — пропуск (нужны данные с API)"
    );

    await detailLink.first().click();
    await expect(page).toHaveURL(/\/event\/.+/, { timeout: 15_000 });
    await expect(page.locator("body")).toBeVisible();
    await expect(page.locator("body")).not.toHaveText("");
  });

  test("кнопки действий видны", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => {});

    const detailLink = page.getByRole("link", {
      name: /подробнее|details/i,
    });
    test.skip(
      (await detailLink.count()) === 0,
      "В ленте нет стартов — пропуск"
    );

    await detailLink.first().click();
    await expect(page).toHaveURL(/\/event\/.+/);

    const body = ((await page.textContent("body")) ?? "").toLowerCase();
    const hasActions =
      body.includes("календар") ||
      body.includes("calendar") ||
      body.includes("еду") ||
      body.includes("join") ||
      body.includes("редактир") ||
      body.includes("edit");
    expect(hasActions).toBeTruthy();
  });
});
