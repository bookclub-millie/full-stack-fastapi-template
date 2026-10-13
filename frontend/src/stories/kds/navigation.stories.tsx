import type { Meta, StoryObj } from '@storybook/react-vite'
import * as Examples from './navigation'

const meta = { title: 'KDS/Components/Navigation' } satisfies Meta
export default meta
type Story = StoryObj<typeof meta>

export const Command: Story = { render: () => <Examples.CommandExample /> }
export const ContextMenu: Story = {
  render: () => <Examples.ContextMenuExample />
}
export const DropdownMenu: Story = {
  render: () => <Examples.DropdownMenuExample />
}
export const Menubar: Story = { render: () => <Examples.MenubarExample /> }
export const NavigationMenu: Story = {
  render: () => <Examples.NavigationMenuExample />
}
export const Sidebar: Story = { render: () => <Examples.SidebarExample /> }
