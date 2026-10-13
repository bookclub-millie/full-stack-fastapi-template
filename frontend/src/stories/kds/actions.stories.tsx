import type { Meta, StoryObj } from '@storybook/react-vite'
import { expect, userEvent, within } from 'storybook/test'
import * as Examples from './actions'

const meta = { title: 'KDS/Components/Actions' } satisfies Meta
export default meta
type Story = StoryObj<typeof meta>

export const Button: Story = { render: () => <Examples.ButtonExample /> }
export const Badge: Story = { render: () => <Examples.BadgeExample /> }
export const Avatar: Story = { render: () => <Examples.AvatarExample /> }
export const Breadcrumb: Story = {
  render: () => <Examples.BreadcrumbExample />
}
export const ButtonGroup: Story = {
  render: () => <Examples.ButtonGroupExample />
}
export const Kbd: Story = { render: () => <Examples.KbdExample /> }
export const Marker: Story = { render: () => <Examples.MarkerExample /> }
export const Toggle: Story = {
  render: () => <Examples.ToggleExample />,
  play: async ({ canvasElement }) => {
    const toggle = within(canvasElement).getByRole('button', {
      name: '즐겨찾기'
    })
    await expect(toggle).toHaveAttribute('aria-pressed', 'true')
    await userEvent.click(toggle)
    await expect(toggle).toHaveAttribute('aria-pressed', 'false')
    await userEvent.keyboard(' ')
    await expect(toggle).toHaveAttribute('aria-pressed', 'true')
  }
}
export const ToggleGroup: Story = {
  render: () => <Examples.ToggleGroupExample />
}
