import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    name: 'unit',
    environment: 'node',
    include: ['src/**/*.test.ts'],
    // JUnit results feed scripts/harness/collect_evidence.py (TC ids in test titles).
    reporters: ['default', 'junit'],
    outputFile: { junit: 'test-results/unit.xml' },
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
