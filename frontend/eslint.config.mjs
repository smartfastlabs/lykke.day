import js from "@eslint/js";
import tseslint from "@typescript-eslint/eslint-plugin";
import tsparser from "@typescript-eslint/parser";
import solid from "eslint-plugin-solid";

export default [
  {
    ignores: [
      "dist/**",
      "node_modules/**",
      "public/**",
      "*.config.*",
      "scripts/**",
    ],
  },
  js.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    plugins: {
      "@typescript-eslint": tseslint,
      solid: solid,
    },
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 2020,
        sourceType: "module",
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: {
        console: "readonly",
        document: "readonly",
        window: "readonly",
        setTimeout: "readonly",
        clearTimeout: "readonly",
        setInterval: "readonly",
        clearInterval: "readonly",
        WebSocket: "readonly",
        Event: "readonly",
        MessageEvent: "readonly",
        CloseEvent: "readonly",
        fetch: "readonly",
        navigator: "readonly",
        TouchEvent: "readonly",
        HTMLElement: "readonly",
        confirm: "readonly",
        btoa: "readonly",
        Notification: "readonly",
        crypto: "readonly",
        ServiceWorkerGlobalScope: "readonly",
        ServiceWorkerRegistration: "readonly",
        PushEvent: "readonly",
        NotificationOptions: "readonly",
        NotificationEvent: "readonly",
        ExtendableEvent: "readonly",
        RequestInit: "readonly",
        URLSearchParams: "readonly",
        localStorage: "readonly",
        sessionStorage: "readonly",
        performance: "readonly",
        PerformanceNavigationTiming: "readonly",
        global: "readonly",
      },
    },
    rules: {
      // TypeScript rules
      "@typescript-eslint/no-unused-vars": [
        "error",
        { 
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          args: "all",
          caughtErrors: "all",
          caughtErrorsIgnorePattern: "^_",
        },
      ],
      "@typescript-eslint/no-explicit-any": "warn",
      "no-unused-vars": "off", // Turn off base rule as it conflicts with @typescript-eslint/no-unused-vars

      // Solid.js rules
      "solid/reactivity": "warn",
      "solid/no-destructure": "warn",
      "solid/jsx-no-undef": "error",

      // General rules
      "no-console": "off",
      "prefer-const": "error",
      "no-var": "error",
    },
  },
];
