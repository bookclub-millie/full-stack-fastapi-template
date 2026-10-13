import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@kds/ui/components/card'
import type { ReactNode } from 'react'

export const Specimen = ({
  name,
  title,
  description,
  children
}: {
  name: string
  title: string
  description: string
  children: ReactNode
}) => {
  return (
    <Card
      id={`specimen-${name}`}
      data-component-example={name}
      aria-labelledby={`specimen-${name}-title`}
      className="gap-0 overflow-hidden border-border/80 bg-card p-0 shadow-none"
    >
      <CardHeader className="gap-1 border-b border-border/70 px-5 py-4">
        <CardTitle
          id={`specimen-${name}-title`}
          className="text-base font-semibold"
        >
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="flex min-h-24 flex-col justify-center gap-3 p-5">
        {children}
      </CardContent>
    </Card>
  )
}
