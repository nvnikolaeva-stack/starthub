import type { NextConfig } from "next";
import path from "path";
import { fileURLToPath } from "url";
import createNextIntlPlugin from "next-intl/plugin";

/** Явный корень проекта: иначе Next может взять родительский lockfile и сломать маршруты (404 на /add). */
const rootDir = path.dirname(fileURLToPath(import.meta.url));

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
  output: "standalone",
  reactCompiler: true,
  turbopack: {
    root: rootDir,
  },
};

export default withNextIntl(nextConfig);
