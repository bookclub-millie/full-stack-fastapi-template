import type { Meta, StoryObj } from '@storybook/react-vite'
import { expect, userEvent, within } from 'storybook/test'
import * as Examples from './forms'
import { InputValidationExample } from './input-validation'
import { SliderSpecimen } from './slider-specimen'

const meta = { title: 'KDS/Components/Forms' } satisfies Meta
export default meta
type Story = StoryObj<typeof meta>

export const Input: Story = { render: () => <Examples.InputExample /> }
export const Field: Story = { render: () => <Examples.FieldExample /> }
export const Label: Story = { render: () => <Examples.LabelExample /> }
export const InputGroup: Story = {
  render: () => <Examples.InputGroupExample />
}
export const InputOtp: Story = { render: () => <Examples.InputOtpExample /> }
export const Checkbox: Story = { render: () => <Examples.CheckboxExample /> }
export const RadioGroup: Story = {
  render: () => <Examples.RadioGroupExample />
}
export const Switch: Story = { render: () => <Examples.SwitchExample /> }
export const Textarea: Story = { render: () => <Examples.TextareaExample /> }
export const Select: Story = { render: () => <Examples.SelectExample /> }
export const NativeSelect: Story = {
  render: () => <Examples.NativeSelectExample />
}
export const Combobox: Story = { render: () => <Examples.ComboboxExample /> }
export const Calendar: Story = { render: () => <Examples.CalendarExample /> }
export const Attachment: Story = {
  render: () => <Examples.AttachmentExample />
}
export const Questionnaire: Story = {
  render: () => <Examples.QuestionnaireExample />
}
export const Direction: Story = { render: () => <Examples.DirectionExample /> }

export const Slider: Story = { render: () => <SliderSpecimen /> }

export const InputValidation: Story = {
  render: () => <InputValidationExample />,
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)
    await userEvent.click(canvas.getByRole('button', { name: 'Save profile' }))
    await expect(canvas.getByRole('alert')).toHaveTextContent(
      'Enter a display name.'
    )
    await expect(canvas.getByLabelText('Display name')).toHaveAttribute(
      'aria-invalid',
      'true'
    )
    await userEvent.type(canvas.getByLabelText('Display name'), 'Ada')
    await userEvent.click(canvas.getByRole('button', { name: 'Save profile' }))
    await expect(canvas.getByRole('status')).toHaveTextContent(
      'Profile saved for Ada.'
    )
    await expect(canvas.queryByRole('alert')).not.toBeInTheDocument()
  }
}
