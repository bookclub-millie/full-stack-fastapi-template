import type { Meta, StoryObj } from '@storybook/react-vite'
import * as Examples from './surfaces'

const meta = { title: 'KDS/Components/Surfaces' } satisfies Meta
export default meta
type Story = StoryObj<typeof meta>

export const Accordion: Story = { render: () => <Examples.AccordionExample /> }
export const AspectRatio: Story = {
  render: () => <Examples.AspectRatioExample />
}
export const Card: Story = { render: () => <Examples.CardExample /> }
export const Collapsible: Story = {
  render: () => <Examples.CollapsibleExample />
}
export const Item: Story = { render: () => <Examples.ItemExample /> }
export const Pagination: Story = {
  render: () => <Examples.PaginationExample />
}
export const Resizable: Story = { render: () => <Examples.ResizableExample /> }
export const ScrollArea: Story = {
  render: () => <Examples.ScrollAreaExample />
}
export const Separator: Story = { render: () => <Examples.SeparatorExample /> }
export const Table: Story = { render: () => <Examples.TableExample /> }
export const Tabs: Story = { render: () => <Examples.TabsExample /> }
