import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import solidPlugin from "vite-plugin-solid";
import devtools from "solid-devtools/vite";
import { existsSync } from "fs";
import { fileURLToPath, URL } from "node:url";

const certPath = "./.certs/master-bedroom.local.pem";
const keyPath = "./.certs/master-bedroom.local-key.pem";
const certsExist = existsSync(certPath) && existsSync(keyPath);

export default defineConfig({
  plugins: [devtools(), solidPlugin(), tailwindcss()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    ...(certsExist && {
      https: {
        cert: certPath,
        key: keyPath,
      },
    }),
    allowedHosts: ["master-bedroom.local", "localhost:5173"],
    proxy: {
      "/api": {
        target: "http://localhost:8080",
        changeOrigin: false,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  build: {
    target: "esnext",
  },
});
