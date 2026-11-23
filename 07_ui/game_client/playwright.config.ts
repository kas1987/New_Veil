import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  use: {
    baseURL: 'http://127.0.0.1:8765',
    headless: true,
  },
  webServer: {
    command: 'python ../../04_runtime/game_api/server.py',
    url: 'http://127.0.0.1:8765/api/runtime/status',
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
})
