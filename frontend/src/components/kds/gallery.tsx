import { Badge } from "@kds/ui/components/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@kds/ui/components/card"
import { Separator } from "@kds/ui/components/separator"
import {
  ArrowUpRight,
  CircleCheck,
  Layers,
  Palette,
  Sparkles,
  TriangleAlert,
} from "lucide-react"
import { lazy, type ReactNode, Suspense } from "react"
import { ActionSpecimens } from "./catalog/actions"
import { FeedbackSpecimens } from "./catalog/feedback"
import { FormSpecimens } from "./catalog/forms"
import { NavigationSpecimens } from "./catalog/navigation"
import { SliderSpecimen } from "./catalog/slider-specimen"
import { SurfaceSpecimens } from "./catalog/surfaces"
import { ThemeModeToggle } from "./theme-mode-toggle"

const ChartSpecimen = lazy(() =>
  import("./catalog/chart-specimen").then((module) => ({
    default: module.ChartSpecimen,
  })),
)

const CarouselSpecimen = lazy(() =>
  import("./catalog/carousel-specimen").then((module) => ({
    default: module.CarouselSpecimen,
  })),
)

const sections = [
  { id: "tokens", number: "01", label: "토큰 기반" },
  { id: "actions", number: "02", label: "액션" },
  { id: "forms", number: "03", label: "입력" },
  { id: "feedback", number: "04", label: "피드백" },
  { id: "navigation", number: "05", label: "탐색" },
  { id: "surfaces", number: "06", label: "표면·데이터" },
  { id: "visuals", number: "07", label: "시각화" },
]

const semanticTokens = [
  { name: "기본 배경", token: "--background-default", kind: "Background" },
  { name: "기본 표면", token: "--surface-primary-01", kind: "Surface" },
  { name: "강조 액션", token: "--fill-accent-primary", kind: "Action" },
  { name: "기본 텍스트", token: "--text-primary", kind: "Text" },
  { name: "보조 경계", token: "--border-secondary-01", kind: "Border" },
  { name: "키보드 포커스", token: "--border-primary-focused", kind: "Focus" },
]

const dataTokens = [
  "--data-visual-default-teal",
  "--data-visual-default-yellow",
  "--data-visual-default-blue",
  "--data-visual-default-purple",
  "--data-visual-default-red",
]

function SectionHeading({
  id,
  number,
  eyebrow,
  title,
  description,
  icon,
}: {
  id: string
  number: string
  eyebrow: string
  title: string
  description: string
  icon: ReactNode
}) {
  return (
    <div className="mb-6 flex items-start gap-4">
      <span className="grid size-10 shrink-0 place-items-center rounded-xl border border-border bg-card text-primary">
        {icon}
      </span>
      <div className="min-w-0">
        <p className="mb-1 font-mono text-[11px] tracking-[0.16em] text-muted-foreground">
          {number} / {eyebrow}
        </p>
        <h2
          id={id}
          className="font-heading text-2xl font-semibold tracking-tight sm:text-3xl"
        >
          {title}
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          {description}
        </p>
      </div>
    </div>
  )
}

function TokenSwatch({
  name,
  token,
  kind,
}: {
  name: string
  token: string
  kind: string
}) {
  return (
    <div className="min-w-0 rounded-xl border border-border/80 bg-card p-2.5">
      <div
        aria-hidden="true"
        className="mb-3 h-14 rounded-lg border border-border/60"
        style={{ backgroundColor: `var(${token})` }}
      />
      <p className="truncate text-xs font-medium">{name}</p>
      <p className="mt-1 truncate font-mono text-[10px] text-muted-foreground">
        {token}
      </p>
      <p className="mt-2 text-[10px] text-muted-foreground">{kind}</p>
    </div>
  )
}

export default function KdsGallery() {
  return (
    <main id="top" className="min-h-svh">
      <a
        className="sr-only z-50 rounded-md bg-background px-4 py-2 text-foreground focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:ring-2 focus:ring-ring"
        href="#tokens"
      >
        본문으로 건너뛰기
      </a>

      <header className="sticky top-0 z-30 border-b border-border/80 bg-background/95 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-[1440px] items-center justify-between px-4 sm:px-6 lg:px-10">
          <a
            aria-label="KDS 2.0 컴포넌트 갤러리 처음으로"
            className="flex items-center gap-3 rounded-md focus-visible:outline-2 focus-visible:outline-ring"
            href="#top"
          >
            <span className="grid size-9 place-items-center rounded-xl bg-primary font-heading text-sm font-bold text-primary-foreground">
              K
            </span>
            <span className="flex flex-col leading-tight">
              <span className="text-xs font-semibold tracking-[0.08em]">
                KT DESIGN SYSTEM
              </span>
              <span className="mt-1 font-mono text-[9px] tracking-[0.16em] text-muted-foreground">
                KDS 2.0 / COMPONENT CATALOG
              </span>
            </span>
          </a>

          <div className="flex items-center gap-3">
            <span className="hidden text-xs text-muted-foreground sm:inline">
              61개 로컬 컴포넌트
            </span>
            <Separator
              aria-hidden="true"
              className="hidden data-[orientation=vertical]:h-5 sm:block"
              orientation="vertical"
            />
            <ThemeModeToggle />
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-[1440px] gap-0 px-0 lg:grid-cols-[210px_minmax(0,1fr)] lg:gap-8 lg:px-10">
        <aside className="hidden lg:block">
          <nav aria-label="갤러리 섹션" className="sticky top-24 px-2 pt-10">
            <p className="mb-4 px-3 font-mono text-[10px] tracking-[0.18em] text-muted-foreground uppercase">
              On this page
            </p>
            <ul className="space-y-1">
              {sections.map((section) => (
                <li key={section.id}>
                  <a
                    className="group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-2 focus-visible:outline-ring"
                    href={`#${section.id}`}
                  >
                    <span className="font-mono text-[10px] text-muted-foreground/70 group-hover:text-primary">
                      {section.number}
                    </span>
                    <span>{section.label}</span>
                  </a>
                </li>
              ))}
            </ul>
            <Separator className="my-5" />
            <div className="px-3 text-xs leading-5 text-muted-foreground">
              <div className="mb-2 flex items-center gap-2 text-foreground">
                <span className="size-1.5 rounded-full bg-primary" />
                Token source
              </div>
              <code className="font-mono text-[10px]">@kds/ui/tokens.css</code>
            </div>
          </nav>
        </aside>

        <div className="min-w-0 px-4 pb-16 sm:px-6 lg:px-0">
          <nav
            aria-label="갤러리 섹션"
            className="-mx-4 flex gap-2 overflow-x-auto border-b border-border/70 px-4 py-3 sm:-mx-6 sm:px-6 lg:hidden"
          >
            {sections.map((section) => (
              <a
                key={section.id}
                className="shrink-0 rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground focus-visible:outline-2 focus-visible:outline-ring"
                href={`#${section.id}`}
              >
                {section.label}
              </a>
            ))}
          </nav>

          <div className="min-w-0">
            <section
              aria-labelledby="intro-title"
              className="grid gap-8 py-10 sm:py-14 lg:grid-cols-[minmax(0,1fr)_260px] lg:items-end lg:gap-12 lg:py-20"
            >
              <div className="max-w-3xl">
                <div className="mb-5 flex flex-wrap items-center gap-2">
                  <Badge variant="outline">AI-readable reference</Badge>
                  <span className="inline-flex items-center gap-1.5 font-mono text-[10px] tracking-[0.12em] text-muted-foreground uppercase">
                    <span className="size-1.5 rounded-full bg-primary" />
                    Local source · KDS tokens
                  </span>
                </div>
                <h1
                  className="max-w-3xl font-heading text-4xl leading-[1.12] font-semibold tracking-[-0.04em] sm:text-5xl lg:text-6xl"
                  id="intro-title"
                >
                  토큰으로 연결하는
                  <br />
                  컴포넌트 카탈로그.
                </h1>
                <p className="mt-6 max-w-2xl text-sm leading-7 text-muted-foreground sm:text-base">
                  실제 shadcn 컴포넌트 전체를 KDS 2.0 의미 토큰으로 확인합니다.
                  각 예시는 로컬 소스, 접근 가능한 기본 동작, 라이트·다크 모드를
                  함께 보여줍니다.
                </p>
                <div className="mt-7 flex flex-wrap items-center gap-3">
                  <a
                    className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 focus-visible:outline-2 focus-visible:outline-ring"
                    href="#actions"
                  >
                    컴포넌트 둘러보기
                    <ArrowUpRight aria-hidden="true" className="size-4" />
                  </a>
                  <span className="text-xs text-muted-foreground">
                    61 component sources · no remote registry
                  </span>
                </div>
              </div>

              <Card className="gap-0 border-border/80 bg-card p-0 shadow-none">
                <CardHeader className="border-b border-border/70 px-5 py-4">
                  <p className="font-mono text-[10px] tracking-[0.16em] text-muted-foreground uppercase">
                    CATALOG SNAPSHOT
                  </p>
                  <CardTitle className="text-base">완성된 로컬 참조</CardTitle>
                  <CardDescription>
                    소스와 예시를 함께 탐색합니다.
                  </CardDescription>
                </CardHeader>
                <CardContent className="grid grid-cols-2 gap-4 p-5">
                  <div>
                    <p className="font-heading text-3xl font-semibold">61</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      컴포넌트
                    </p>
                  </div>
                  <div>
                    <p className="font-heading text-3xl font-semibold">2</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      KDS 모드
                    </p>
                  </div>
                  <div className="col-span-2 flex items-center gap-2 border-t border-border/70 pt-4 text-xs text-muted-foreground">
                    <CircleCheck
                      aria-hidden="true"
                      className="size-4 text-primary"
                    />
                    오프라인에서 읽을 수 있는 소스·사용 인덱스
                  </div>
                </CardContent>
              </Card>
            </section>

            <section
              aria-labelledby="tokens-title"
              className="scroll-mt-32 border-t border-border/80 py-10 sm:py-14"
              id="tokens"
            >
              <SectionHeading
                id="tokens-title"
                description="공급된 KDS 토큰이 색의 단일 출처입니다. 모드를 바꾸면 같은 의미 변수의 값이 함께 바뀝니다."
                eyebrow="FOUNDATION"
                icon={<Palette aria-hidden="true" className="size-4" />}
                number="01"
                title="KDS 토큰이 색을 결정합니다."
              />
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
                {semanticTokens.map((item) => (
                  <TokenSwatch key={item.token} {...item} />
                ))}
              </div>
              <Card className="mt-4 gap-0 border-border/80 bg-card p-0 shadow-none">
                <CardHeader className="px-5 py-4">
                  <CardTitle className="text-sm">Data-visual series</CardTitle>
                  <CardDescription>
                    차트와 데이터 예시는 공급된 KDS 시각화 색상을 사용합니다.
                  </CardDescription>
                </CardHeader>
                <CardContent className="grid grid-cols-2 gap-3 border-t border-border/70 p-5 sm:grid-cols-5">
                  {dataTokens.map((token) => (
                    <div key={token} className="min-w-0">
                      <span
                        aria-hidden="true"
                        className="mb-2 block h-8 rounded-md border border-border/60"
                        style={{ backgroundColor: `var(${token})` }}
                      />
                      <code className="block truncate font-mono text-[10px] text-muted-foreground">
                        {token}
                      </code>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </section>

            <section
              aria-labelledby="actions-title"
              className="scroll-mt-32 border-t border-border/80 py-10 sm:py-14"
              id="actions"
            >
              <SectionHeading
                id="actions-title"
                description="액션의 위계, 라벨, 단축키와 선택 상태를 실제 컴포넌트로 비교합니다."
                eyebrow="ACTIONS"
                icon={<Sparkles aria-hidden="true" className="size-4" />}
                number="02"
                title="명확한 액션과 상태."
              />
              <ActionSpecimens />
            </section>

            <section
              aria-labelledby="forms-title"
              className="scroll-mt-32 border-t border-border/80 py-10 sm:py-14"
              id="forms"
            >
              <SectionHeading
                id="forms-title"
                description="모든 입력에는 보이는 이름과 의미 있는 상태가 있습니다. 키보드·포인터 조작을 직접 확인하세요."
                eyebrow="FORM CONTROLS"
                icon={<Layers aria-hidden="true" className="size-4" />}
                number="03"
                title="예측 가능한 입력."
              />
              <FormSpecimens slider={<SliderSpecimen />} />
            </section>

            <section
              aria-labelledby="feedback-title"
              className="scroll-mt-32 border-t border-border/80 py-10 sm:py-14"
              id="feedback"
            >
              <SectionHeading
                id="feedback-title"
                description="상태 메시지와 오버레이는 포커스를 관리하고 KDS 모드에 맞는 토큰을 사용합니다."
                eyebrow="FEEDBACK & OVERLAYS"
                icon={<CircleCheck aria-hidden="true" className="size-4" />}
                number="04"
                title="상태를 놓치지 않게."
              />
              <FeedbackSpecimens />
            </section>

            <section
              aria-labelledby="navigation-title"
              className="scroll-mt-32 border-t border-border/80 py-10 sm:py-14"
              id="navigation"
            >
              <SectionHeading
                id="navigation-title"
                description="명령 검색, 컨텍스트 메뉴, 계층 탐색과 접이식 사이드바를 시험합니다."
                eyebrow="NAVIGATION"
                icon={<ArrowUpRight aria-hidden="true" className="size-4" />}
                number="05"
                title="이동과 탐색."
              />
              <NavigationSpecimens />
            </section>

            <section
              aria-labelledby="surfaces-title"
              className="scroll-mt-32 border-t border-border/80 py-10 sm:py-14"
              id="surfaces"
            >
              <SectionHeading
                id="surfaces-title"
                description="표면, 경계, 표와 탭은 같은 KDS 변수 체계 안에서 계층을 만듭니다."
                eyebrow="SURFACES & DATA"
                icon={<Layers aria-hidden="true" className="size-4" />}
                number="06"
                title="정보를 담는 구조."
              />
              <SurfaceSpecimens />
            </section>

            <section
              aria-labelledby="visuals-title"
              className="scroll-mt-32 border-t border-border/80 py-10 sm:py-14"
              id="visuals"
            >
              <SectionHeading
                id="visuals-title"
                description="가벼운 차트와 캐러셀은 별도 청크로 분리되며 데이터 색은 KDS 시각화 토큰에서 옵니다."
                eyebrow="VISUALIZATION"
                icon={<TriangleAlert aria-hidden="true" className="size-4" />}
                number="07"
                title="무거운 예시는 필요한 때에."
              />
              <div className="grid gap-4 xl:grid-cols-2">
                <Suspense
                  fallback={
                    <div className="grid min-h-56 place-items-center rounded-xl border border-border bg-card text-sm text-muted-foreground">
                      차트 컴포넌트를 불러오는 중…
                    </div>
                  }
                >
                  <ChartSpecimen />
                </Suspense>
                <Suspense
                  fallback={
                    <div className="grid min-h-56 place-items-center rounded-xl border border-border bg-card text-sm text-muted-foreground">
                      캐러셀 컴포넌트를 불러오는 중…
                    </div>
                  }
                >
                  <CarouselSpecimen />
                </Suspense>
              </div>
            </section>

            <footer className="flex flex-col gap-2 border-t border-border/80 py-6 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
              <span className="font-mono tracking-[0.1em]">
                KDS 2.0 · LOCAL COMPONENT CATALOG
              </span>
              <a
                className="inline-flex w-fit items-center gap-1.5 font-medium text-foreground hover:text-primary focus-visible:outline-2 focus-visible:outline-ring"
                href="#top"
              >
                처음으로
                <ArrowUpRight aria-hidden="true" className="size-3.5" />
              </a>
            </footer>
          </div>
        </div>
      </div>
    </main>
  )
}
