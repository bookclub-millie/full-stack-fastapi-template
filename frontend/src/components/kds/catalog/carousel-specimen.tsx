import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@kds/ui/components/carousel"
import { Specimen } from "./specimen"

const samples = [
  { title: "표면", token: "--surface-primary-01" },
  { title: "텍스트", token: "--text-primary" },
  { title: "포커스", token: "--border-primary-focused" },
]

export function CarouselSpecimen() {
  return (
    <Specimen
      name="carousel"
      title="Carousel"
      description="Move between generic token cards with labelled previous and next controls."
    >
      <Carousel
        aria-label="토큰 예시 슬라이드"
        className="mx-auto w-full max-w-lg"
      >
        <CarouselContent>
          {samples.map((sample) => (
            <CarouselItem key={sample.token}>
              <div className="grid min-h-28 content-center gap-2 rounded-lg border border-border bg-muted/30 p-4 text-center">
                <span className="font-medium">{sample.title}</span>
                <code className="text-xs text-muted-foreground">
                  {sample.token}
                </code>
              </div>
            </CarouselItem>
          ))}
        </CarouselContent>
        <div className="mt-3 flex justify-center gap-2">
          <CarouselPrevious className="static translate-y-0" />
          <CarouselNext className="static translate-y-0" />
        </div>
      </Carousel>
    </Specimen>
  )
}
