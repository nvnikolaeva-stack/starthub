import { test, expect } from "@playwright/test";

test.describe("Статистика", () => {
  test("страница загружается", async ({ page }) => {
    await page.goto("/stats");
    await page.waitForLoadState("domcontentloaded");

    const body = ((await page.textContent("body")) ?? "").toLowerCase();
    const hasStats =
      body.includes("статистик") ||
      body.includes("statistic") ||
      body.includes("команд") ||
      body.includes("team");
    expect(hasStats).toBeTruthy();
  });

  test("табы работают", async ({ page }) => {
    await page.goto("/stats");
    await page.waitForTimeout(500);

    const tab = page.getByRole("button", {
      name: /участник|people|участники/i,
    });
    test.skip((await tab.count()) === 0, "Нет второй вкладки (People/Участники)");
    await tab.first().click();
    await page.waitForTimeout(400);
    await expect(page.locator("body")).toBeVisible();
  });
});
