import type { Meta, StoryObj } from '@storybook/react-vite'
import { CarouselSpecimen } from './carousel-specimen'
import { ChartSpecimen } from './chart-specimen'

const meta = { title: 'KDS/Components/Data' } satisfies Meta
export default meta
type Story = StoryObj<typeof meta>

export const Chart: Story = { render: () => <ChartSpecimen /> }
export const Carousel: Story = { render: () => <CarouselSpecimen /> }
