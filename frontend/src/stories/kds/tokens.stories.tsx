import type { Meta, StoryObj } from '@storybook/react-vite'
import { Specimen } from './specimen'

const meta = { title: 'KDS/Tokens' } satisfies Meta
export default meta
type Story = StoryObj<typeof meta>

const tokens = [
  ['Surface', '--surface-primary-01'],
  ['Text', '--text-primary'],
  ['Focus', '--border-primary-focused'],
  ['Critical', '--text-feedback-critical-01'],
  ['Chart 1', '--chart-1'],
  ['Chart 2', '--chart-2'],
  ['Chart 3', '--chart-3'],
  ['Chart 4', '--chart-4'],
  ['Chart 5', '--chart-5']
] as const

export const Semantic: Story = {
  render: () => (
    <Specimen
      name="tokens"
      title="Semantic tokens"
      description="The theme toolbar changes these live CSS custom properties."
    >
      <dl className="grid gap-4 sm:grid-cols-2">
        {tokens.map(([name, token]) => (
          <div key={token} className="rounded-lg border border-border p-3">
            <div
              aria-hidden="true"
              className="mb-3 h-12 rounded border border-border"
              style={{ backgroundColor: `var(${token})` }}
            />
            <dt className="font-medium">{name}</dt>
            <dd>
              <code className="text-xs text-muted-foreground">{token}</code>
            </dd>
          </div>
        ))}
      </dl>
    </Specimen>
  )
}
