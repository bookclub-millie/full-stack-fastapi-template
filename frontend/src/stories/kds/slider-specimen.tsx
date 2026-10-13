import { Slider } from '@kds/ui/components/slider'
import { useState } from 'react'
import { Specimen } from './specimen'

const getSpacingAriaLabel = () => '간격 크기'

export const SliderSpecimen = () => {
  const [value, setValue] = useState(64)

  return (
    <Specimen
      name="slider"
      title="Slider"
      description="A keyboard-adjustable numeric range with an accessible label."
    >
      <div className="grid gap-4">
        <span className="text-sm leading-none font-medium">간격 크기</span>
        <Slider
          getAriaLabel={getSpacingAriaLabel}
          max={100}
          onValueChange={nextValue =>
            setValue(
              typeof nextValue === 'number' ? nextValue : (nextValue[0] ?? 0)
            )
          }
          value={[value]}
        />
        <output className="text-xs text-muted-foreground">{value} / 100</output>
      </div>
    </Specimen>
  )
}
