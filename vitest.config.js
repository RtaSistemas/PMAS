import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    include: ['tests/frontend/unit/**/*.test.js'],
    coverage: {
      provider: 'v8',
      include: ['frontend/utils.js'],
      reporter: ['text', 'lcov'],
    },
  },
});
