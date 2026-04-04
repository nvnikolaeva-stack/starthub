import { test, expect } from "@playwright/test";

test.describe("Локаль", () => {
  test("интерфейс на русском, переключателя EN нет", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");

    await expect(
      page.getByRole("heading", { name: "Календарь стартов" })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /english/i })).toHaveCount(0);
    await expect(page.getByText("EN", { exact: true })).toHaveCount(0);
  });
});
