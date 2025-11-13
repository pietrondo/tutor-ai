import type { Meta, StoryObj } from '@storybook/react'
import { Button } from './Button'
import { Play } from 'lucide-react'

const meta: Meta<typeof Button> = {
  title: 'Design System/Button',
  component: Button,
}

export default meta
type Story = StoryObj<typeof Button>

export const Primary: Story = {
  args: {
    children: 'Primary',
    variant: 'primary',
  },
}

export const AccentWithIcon: Story = {
  args: {
    children: 'Accent',
    variant: 'accent',
    icon: <Play />,
  },
}

export const Loading: Story = {
  args: {
    children: 'Loading',
    loading: true,
  },
}
