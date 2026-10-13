import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    name: 'unit',
    environment: 'node',
    include: ['src/**/*.test.ts'],
    // test-results/unit.json feeds scripts/harness/collect_evidence.py (TC evidence).
    reporters: ['default', './evidence-reporter.ts'],
    coverage: {
      provider: 'v8',
      include: ['src/lib/env.ts', 'src/utils.ts'],
      reporter: ['text', 'html', 'lcov'],
      thresholds: {
        lines: 90,
        functions: 90,
        branches: 90,
        statements: 90
      }
    }
  }
})
