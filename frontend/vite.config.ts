import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  return {
    plugins: [react()],
    server: {
      port: Number(env.VITE_DEV_PORT || 5173),
      host: "0.0.0.0",
    },
    build: {
      outDir: "dist",
      // Performance optimizations for Raspberry Pi deployment
      rollupOptions: {
        output: {
          // Split vendor code from app code for better caching
          manualChunks: {
            vendor: ["react", "react-dom"],
            ui: ["dayjs", "clsx"],
            network: ["axios"],
          },
        },
      },
      // Optimize chunk size
      chunkSizeWarningLimit: 1000,
      // Use terser for better compression
      minify: "terser",
      terserOptions: {
        compress: {
          drop_console: mode === "production", // Remove console.logs in production
        },
      },
      // Source maps only in development
      sourcemap: mode === "development",
    },
  };
});
