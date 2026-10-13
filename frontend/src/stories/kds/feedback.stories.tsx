import type { Meta, StoryObj } from '@storybook/react-vite'
import { expect, userEvent, waitFor, within } from 'storybook/test'
import * as Examples from './feedback'

const meta = { title: 'KDS/Components/Feedback' } satisfies Meta
export default meta
type Story = StoryObj<typeof meta>

export const Alert: Story = { render: () => <Examples.AlertExample /> }
export const AlertDialog: Story = {
  render: () => <Examples.AlertDialogExample />
}
export const Bubble: Story = { render: () => <Examples.BubbleExample /> }
export const Dialog: Story = {
  render: () => <Examples.DialogExample />,
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)
    const page = within(canvasElement.ownerDocument.body)
    const trigger = canvas.getByRole('button', { name: '상세 보기' })
    await userEvent.click(trigger)
    const dialog = await page.findByRole('dialog', { name: '시맨틱 색상' })
    await waitFor(() =>
      expect(dialog.contains(canvasElement.ownerDocument.activeElement)).toBe(
        true
      )
    )
    await userEvent.click(
      within(dialog).getByRole('button', { name: /^닫기$/ })
    )
    await waitFor(() => expect(dialog).not.toBeInTheDocument())
    await waitFor(() => expect(trigger).toHaveFocus())
    await userEvent.click(trigger)
    const reopenedDialog = await page.findByRole('dialog', {
      name: '시맨틱 색상'
    })
    await userEvent.keyboard('{Escape}')
    await waitFor(() => expect(reopenedDialog).not.toBeInTheDocument())
    await waitFor(() => expect(trigger).toHaveFocus())
  }
}
export const Drawer: Story = { render: () => <Examples.DrawerExample /> }
export const Empty: Story = { render: () => <Examples.EmptyExample /> }
export const HoverCard: Story = { render: () => <Examples.HoverCardExample /> }
export const Message: Story = { render: () => <Examples.MessageExample /> }
export const MessageScroller: Story = {
  render: () => <Examples.MessageScrollerExample />
}
export const Popover: Story = { render: () => <Examples.PopoverExample /> }
export const Progress: Story = { render: () => <Examples.ProgressExample /> }
export const Sheet: Story = { render: () => <Examples.SheetExample /> }
export const Skeleton: Story = { render: () => <Examples.SkeletonExample /> }
export const Spinner: Story = { render: () => <Examples.SpinnerExample /> }
export const Toast: Story = { render: () => <Examples.ToastExample /> }
export const Tooltip: Story = { render: () => <Examples.TooltipExample /> }
