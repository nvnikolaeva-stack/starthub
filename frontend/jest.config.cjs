/** @type {import("jest").Config} */
module.exports = {
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  transform: {
    "^.+\\.(tsx?|jsx?)$": [
      "ts-jest",
      {
        tsconfig: {
          jsx: "react-jsx",
          module: "commonjs",
          moduleResolution: "node",
          esModuleInterop: true,
          resolveJsonModule: true,
          allowJs: true,
          strict: true,
          target: "ES2017",
          lib: ["dom", "esnext"],
          skipLibCheck: true,
          baseUrl: ".",
          paths: { "@/*": ["./src/*"] },
        },
      },
    ],
  },
  testPathIgnorePatterns: ["<rootDir>/.next/", "<rootDir>/node_modules/"],
  // next-intl / use-intl — ESM; не исключаем их из трансформации
  transformIgnorePatterns: [
    "/node_modules/(?!(@formatjs|next-intl|use-intl|intl-messageformat)/)",
  ],
};
