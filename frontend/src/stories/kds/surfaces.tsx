import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger
} from '@kds/ui/components/accordion'
import { AspectRatio } from '@kds/ui/components/aspect-ratio'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@kds/ui/components/card'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger
} from '@kds/ui/components/collapsible'
import {
  Item,
  ItemActions,
  ItemContent,
  ItemDescription,
  ItemMedia,
  ItemTitle
} from '@kds/ui/components/item'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious
} from '@kds/ui/components/pagination'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup
} from '@kds/ui/components/resizable'
import { ScrollArea } from '@kds/ui/components/scroll-area'
import { Separator } from '@kds/ui/components/separator'
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@kds/ui/components/table'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger
} from '@kds/ui/components/tabs'
import { Layers, Palette } from 'lucide-react'
import { Specimen } from './specimen'

export const AccordionExample = () => {
  return (
    <Specimen
      name="accordion"
      title="Accordion"
      description="Expand a keyboard-operable item to reveal its supporting text."
    >
      <Accordion defaultValue={['semantic']} className="w-full">
        <AccordionItem value="semantic">
          <AccordionTrigger>시맨틱 토큰이란?</AccordionTrigger>
          <AccordionContent>
            <p>
              컴포넌트 역할을 이름으로 표현하며, KDS 모드가 실제 값을
              결정합니다.
            </p>
          </AccordionContent>
        </AccordionItem>
        <AccordionItem value="mode">
          <AccordionTrigger>다크 모드는 어떻게 적용되나요?</AccordionTrigger>
          <AccordionContent>
            <p>같은 CSS 변수가 `data-mode`에 따라 다른 토큰 값을 참조합니다.</p>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </Specimen>
  )
}

export const AspectRatioExample = () => {
  return (
    <Specimen
      name="aspect-ratio"
      title="Aspect Ratio"
      description="A media placeholder maintains its declared 16:9 geometry."
    >
      <AspectRatio
        ratio={16 / 9}
        className="grid place-items-center rounded-lg border border-border bg-muted/50"
      >
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Palette aria-hidden="true" className="size-4" />
          KDS preview
        </div>
      </AspectRatio>
    </Specimen>
  )
}

export const CardExample = () => {
  return (
    <Specimen
      name="card"
      title="Card"
      description="Surface, hierarchy, and content spacing use the KDS semantic map."
    >
      <Card className="border-border/80 shadow-none">
        <CardHeader>
          <CardTitle className="text-base">기본 표면</CardTitle>
          <CardDescription>var(--surface-primary-01)</CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          모드를 바꾸어 표면과 경계의 대비를 확인합니다.
        </CardContent>
      </Card>
    </Specimen>
  )
}

export const CollapsibleExample = () => {
  return (
    <Specimen
      name="collapsible"
      title="Collapsible"
      description="A disclosure reveals content without leaving the current context."
    >
      <Collapsible defaultOpen className="grid gap-2">
        <CollapsibleTrigger className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-sm font-medium focus-visible:outline-2 focus-visible:outline-ring">
          토큰 세부 정보
          <span aria-hidden="true">−</span>
        </CollapsibleTrigger>
        <CollapsibleContent className="rounded-lg bg-muted/50 p-3 text-sm text-muted-foreground">
          기본 표면 토큰은 라이트·다크 모드에서 서로 다른 값을 사용합니다.
        </CollapsibleContent>
      </Collapsible>
    </Specimen>
  )
}

export const ItemExample = () => {
  return (
    <Specimen
      name="item"
      title="Item"
      description="A content row composes icon, description, and a secondary action."
    >
      <Item variant="outline">
        <ItemMedia variant="icon">
          <Layers aria-hidden="true" />
        </ItemMedia>
        <ItemContent>
          <ItemTitle>시맨틱 색상</ItemTitle>
          <ItemDescription>표면과 텍스트의 역할별 토큰</ItemDescription>
        </ItemContent>
        <ItemActions>
          <span className="text-xs text-muted-foreground">6개</span>
        </ItemActions>
      </Item>
    </Specimen>
  )
}

export const PaginationExample = () => {
  return (
    <Specimen
      name="pagination"
      title="Pagination"
      description="Current page is announced, and links expose Korean names."
    >
      <Pagination aria-label="예시 페이지 탐색">
        <PaginationContent>
          <PaginationItem>
            <PaginationPrevious
              aria-label="이전 페이지"
              href="https://example.com/components"
              text="이전"
            />
          </PaginationItem>
          <PaginationItem>
            <PaginationLink href="https://example.com/components">
              1
            </PaginationLink>
          </PaginationItem>
          <PaginationItem>
            <PaginationLink
              aria-label="현재 페이지, 2"
              href="https://example.com/components"
              isActive
            >
              2
            </PaginationLink>
          </PaginationItem>
          <PaginationItem>
            <PaginationLink href="https://example.com/components">
              3
            </PaginationLink>
          </PaginationItem>
          <PaginationItem>
            <PaginationEllipsis />
          </PaginationItem>
          <PaginationItem>
            <PaginationNext
              aria-label="다음 페이지"
              href="https://example.com/components"
              text="다음"
            />
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    </Specimen>
  )
}

export const ResizableExample = () => {
  return (
    <Specimen
      name="resizable"
      title="Resizable Panels"
      description="The divider can be dragged or focused for keyboard resizing."
    >
      <ResizablePanelGroup
        orientation="horizontal"
        className="min-h-28 rounded-lg border border-border"
      >
        <ResizablePanel defaultSize={58} minSize={30}>
          <div className="grid h-full place-items-center p-3 text-sm">
            주요 패널
          </div>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={42} minSize={25}>
          <div className="grid h-full place-items-center bg-muted/50 p-3 text-sm">
            보조 패널
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </Specimen>
  )
}

export const ScrollAreaExample = () => {
  return (
    <Specimen
      name="scroll-area"
      title="Scroll Area"
      description="A labelled scroll viewport contains long content and a visible scrollbar."
    >
      <ScrollArea
        aria-label="토큰 목록"
        role="region"
        className="h-36 rounded-lg border border-border p-3"
      >
        <ul className="grid gap-2 text-sm">
          <li>--background-default</li>
          <li>--surface-primary-01</li>
          <li>--fill-accent-primary</li>
          <li>--text-primary</li>
          <li>--text-secondary-01</li>
          <li>--border-primary-focused</li>
          <li>--data-visual-default-teal</li>
        </ul>
      </ScrollArea>
    </Specimen>
  )
}

export const SeparatorExample = () => {
  return (
    <Specimen
      name="separator"
      title="Separator"
      description="Horizontal and vertical rules provide non-color grouping cues."
    >
      <div className="grid gap-4 text-sm">
        <div className="flex items-center gap-4">
          <span>Foundation</span>
          <Separator
            aria-hidden="true"
            orientation="vertical"
            className="h-5"
          />
          <span className="text-muted-foreground">Components</span>
        </div>
        <div className="grid gap-2">
          <span>기본 값</span>
          <Separator aria-hidden="true" />
          <span className="text-muted-foreground">보조 값</span>
        </div>
      </div>
    </Specimen>
  )
}

export const TableExample = () => {
  return (
    <Specimen
      name="table"
      title="Table"
      description="Column headers and captions keep sample data understandable."
    >
      <Table>
        <TableCaption>KDS semantic token sample</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>역할</TableHead>
            <TableHead>토큰</TableHead>
            <TableHead className="text-right">상태</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell className="font-medium">표면</TableCell>
            <TableCell className="font-mono text-xs">
              --surface-primary-01
            </TableCell>
            <TableCell className="text-right">연결됨</TableCell>
          </TableRow>
          <TableRow>
            <TableCell className="font-medium">포커스</TableCell>
            <TableCell className="font-mono text-xs">
              --border-primary-focused
            </TableCell>
            <TableCell className="text-right">연결됨</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </Specimen>
  )
}

export const TabsExample = () => {
  return (
    <Specimen
      name="tabs"
      title="Tabs"
      description="Arrow-key tab navigation changes the visible content panel."
    >
      <Tabs defaultValue="surface" className="w-full">
        <TabsList className="w-full">
          <TabsTrigger value="surface">Surface</TabsTrigger>
          <TabsTrigger value="text">Text</TabsTrigger>
          <TabsTrigger value="status">Status</TabsTrigger>
        </TabsList>
        <TabsContent
          value="surface"
          className="pt-3 text-sm text-muted-foreground"
        >
          var(--surface-primary-01)
        </TabsContent>
        <TabsContent
          value="text"
          className="pt-3 text-sm text-muted-foreground"
        >
          var(--text-primary)
        </TabsContent>
        <TabsContent
          value="status"
          className="pt-3 text-sm text-muted-foreground"
        >
          var(--text-feedback-critical-01)
        </TabsContent>
      </Tabs>
    </Specimen>
  )
}
