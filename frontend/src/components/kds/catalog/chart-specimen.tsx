import { Bar, BarChart, CartesianGrid, XAxis } from "recharts"

import { Specimen } from "./specimen"
import type { ChartConfig } from "@kds/ui/components/chart"
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@kds/ui/components/chart"

const chartData = [
  { family: "액션", components: 9 },
  { family: "입력", components: 17 },
  { family: "피드백", components: 16 },
  { family: "탐색", components: 6 },
  { family: "표면", components: 11 },
  { family: "시각화", components: 2 },
]

const chartConfig = {
  components: {
    label: "컴포넌트 수",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig

export function ChartSpecimen() {
  return (
    <Specimen
      name="chart"
      title="Chart"
      description="Generic catalog counts use the KDS data-visual series, not literal colors."
    >
      <ChartContainer
        aria-label="카테고리별 컴포넌트 개수 막대 차트"
        className="min-h-56 w-full"
        config={chartConfig}
        role="img"
      >
        <BarChart
          accessibilityLayer
          data={chartData}
          margin={{ left: 4, right: 4 }}
        >
          <CartesianGrid vertical={false} />
          <XAxis
            axisLine={false}
            dataKey="family"
            tickLine={false}
            tickMargin={8}
          />
          <ChartTooltip
            cursor={false}
            content={<ChartTooltipContent indicator="dashed" />}
          />
          <ChartLegend content={<ChartLegendContent />} />
          <Bar dataKey="components" fill="var(--color-components)" radius={4} />
        </BarChart>
      </ChartContainer>
    </Specimen>
  )
}
