import type { Meta, StoryObj } from '@storybook/react'
import { Typography } from './Typography'

const meta: Meta<typeof Typography> = {
  title: 'Design System/Typography',
  component: Typography,
}

export default meta
type Story = StoryObj<typeof Typography>

export const Heading: Story = {
  args: {
    as: 'h2',
    variant: 'h2',
    children: 'Titolo di sezione',
  },
}

export const BodyMuted: Story = {
  args: {
    variant: 'body',
    muted: true,
    children: 'Testo descrittivo con tono neutro e leggibile.',
  },
}

export const Code: Story = {
  args: {
    variant: 'code',
    children: 'const x = 42',
  },
}
