// Writes test-results/unit.json for scripts/harness/collect_evidence.py.
// It records each test's own title (TC ids belong there, not in describe blocks)
// and whether the test was an expected failure (`fails`) or passed only after a
// retry (flaky). JUnit shows both as a plain pass, so it cannot be used as evidence.
import { mkdirSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import type { Reporter, TestCase, Vitest } from 'vitest/node'

const OUTPUT = 'test-results/unit.json'

export default class EvidenceReporter implements Reporter {
  private root = process.cwd()
  private readonly tests: Record<string, unknown>[] = []

  onInit(vitest: Vitest) {
    this.root = vitest.config.root
  }

  onTestCaseResult(testCase: TestCase) {
    this.tests.push({
      file: testCase.module.relativeModuleId,
      title: testCase.name,
      fullName: testCase.fullName,
      state: testCase.result().state,
      fails: testCase.options.fails === true,
      flaky: testCase.diagnostic()?.flaky === true
    })
  }

  onTestRunEnd() {
    const output = resolve(this.root, OUTPUT)
    mkdirSync(dirname(output), { recursive: true })
    writeFileSync(output, `${JSON.stringify({ tests: this.tests }, null, 2)}\n`)
  }
}
