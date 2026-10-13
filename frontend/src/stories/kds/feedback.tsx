import { Alert, AlertDescription, AlertTitle } from '@kds/ui/components/alert'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger
} from '@kds/ui/components/alert-dialog'
import {
  Bubble,
  BubbleContent,
  BubbleGroup,
  BubbleReactions
} from '@kds/ui/components/bubble'
import { Button } from '@kds/ui/components/button'
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@kds/ui/components/dialog'
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger
} from '@kds/ui/components/drawer'
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle
} from '@kds/ui/components/empty'
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger
} from '@kds/ui/components/hover-card'
import {
  Message,
  MessageAvatar,
  MessageContent,
  MessageGroup,
  MessageHeader
} from '@kds/ui/components/message'
import {
  MessageScroller,
  MessageScrollerContent,
  MessageScrollerItem,
  MessageScrollerProvider,
  MessageScrollerViewport
} from '@kds/ui/components/message-scroller'
import {
  Popover,
  PopoverContent,
  PopoverDescription,
  PopoverTitle,
  PopoverTrigger
} from '@kds/ui/components/popover'
import { Progress } from '@kds/ui/components/progress'
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger
} from '@kds/ui/components/sheet'
import { Skeleton } from '@kds/ui/components/skeleton'
import { Spinner } from '@kds/ui/components/spinner'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '@kds/ui/components/tooltip'
import { CircleHelp, TriangleAlert } from 'lucide-react'
import { Specimen } from './specimen'
import { ToastDemo } from './toast-demo'

export const AlertExample = () => {
  return (
    <Specimen
      name="alert"
      title="Alert"
      description="Status tone is communicated by text and icon, not color alone."
    >
      <Alert variant="destructive">
        <TriangleAlert aria-hidden="true" />
        <AlertTitle>토큰을 확인하세요</AlertTitle>
        <AlertDescription>
          참조되지 않는 의미 토큰이 있습니다. 이름과 사용 위치를 확인하세요.
        </AlertDescription>
      </Alert>
    </Specimen>
  )
}

export const AlertDialogExample = () => {
  return (
    <Specimen
      name="alert-dialog"
      title="Alert Dialog"
      description="A destructive confirmation keeps focus in a modal until a choice is made."
    >
      <AlertDialog>
        <AlertDialogTrigger render={<Button variant="destructive" />}>
          초기화 확인
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>설정을 초기화할까요?</AlertDialogTitle>
            <AlertDialogDescription>
              이 예시의 선택은 저장된 정보에 영향을 주지 않습니다.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction>계속</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Specimen>
  )
}

export const BubbleExample = () => {
  return (
    <Specimen
      name="bubble"
      title="Bubble"
      description="Conversation bubbles show alignment and tone without domain-specific data."
    >
      <BubbleGroup>
        <Bubble>
          <BubbleContent>시맨틱 토큰 예시입니다.</BubbleContent>
          <BubbleReactions role="group" aria-label="반응 수">
            <span aria-hidden="true">✓</span>
            <span className="sr-only">확인 1개</span>
          </BubbleReactions>
        </Bubble>
        <Bubble align="end" variant="secondary">
          <BubbleContent>현재 모드에서 확인할 수 있어요.</BubbleContent>
        </Bubble>
      </BubbleGroup>
    </Specimen>
  )
}

export const DialogExample = () => {
  return (
    <Specimen
      name="dialog"
      title="Dialog"
      description="The modal can be opened, dismissed, and closed from its labelled controls."
    >
      <Dialog>
        <DialogTrigger render={<Button variant="outline" />}>
          상세 보기
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>시맨틱 색상</DialogTitle>
            <DialogDescription>
              표면, 텍스트, 포커스 색은 현재 KDS 모드의 토큰에서 옵니다.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose render={<Button variant="outline" />}>
              닫기
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Specimen>
  )
}

export const DrawerExample = () => {
  return (
    <Specimen
      name="drawer"
      title="Drawer"
      description="A touch-friendly modal panel can be opened and dismissed with its close action."
    >
      <Drawer>
        <DrawerTrigger render={<Button variant="outline" />}>
          아래에서 열기
        </DrawerTrigger>
        <DrawerContent>
          <DrawerHeader>
            <DrawerTitle>컴포넌트 정보</DrawerTitle>
            <DrawerDescription>
              이 패널은 KDS 의미 토큰만 사용합니다.
            </DrawerDescription>
          </DrawerHeader>
          <DrawerFooter>
            <DrawerClose render={<Button variant="outline" />}>
              닫기
            </DrawerClose>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    </Specimen>
  )
}

export const EmptyExample = () => {
  return (
    <Specimen
      name="empty"
      title="Empty State"
      description="An empty result includes a clear next step and helpful explanation."
    >
      <Empty className="min-h-40 border">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <CircleHelp aria-hidden="true" />
          </EmptyMedia>
          <EmptyTitle>결과가 없습니다</EmptyTitle>
          <EmptyDescription>
            다른 키워드를 입력하거나 필터를 지워 보세요.
          </EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
          <Button size="sm" variant="outline">
            필터 지우기
          </Button>
        </EmptyContent>
      </Empty>
    </Specimen>
  )
}

export const HoverCardExample = () => {
  return (
    <Specimen
      name="hover-card"
      title="Hover Card"
      description="Supplementary content is available on hover and keyboard focus."
    >
      <HoverCard>
        <HoverCardTrigger render={<Button variant="link" />}>
          토큰 설명
        </HoverCardTrigger>
        <HoverCardContent>
          <p className="font-medium">--surface-primary-01</p>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            기본 콘텐츠 표면에 사용되는 KDS 의미 토큰입니다.
          </p>
        </HoverCardContent>
      </HoverCard>
    </Specimen>
  )
}

export const MessageExample = () => {
  return (
    <Specimen
      name="message"
      title="Message"
      description="Message alignment and metadata remain understandable without avatars."
    >
      <MessageGroup>
        <Message>
          <MessageAvatar aria-hidden="true">K</MessageAvatar>
          <MessageContent>
            <MessageHeader>컴포넌트 카탈로그 · 10:24</MessageHeader>
            <p className="rounded-xl bg-muted px-3 py-2 text-sm">
              메시지 내용은 자동으로 줄바꿈됩니다.
            </p>
          </MessageContent>
        </Message>
      </MessageGroup>
    </Specimen>
  )
}

export const MessageScrollerExample = () => {
  return (
    <Specimen
      name="message-scroller"
      title="Message Scroller"
      description="Scrollable message content keeps a stable viewport and scroll anchor."
    >
      <MessageScrollerProvider>
        <MessageScroller className="h-44 rounded-lg border border-border p-3">
          <MessageScrollerViewport>
            <MessageScrollerContent>
              <MessageScrollerItem>
                <p className="rounded-lg bg-muted p-3 text-sm">
                  첫 번째 메시지 · 위로 스크롤할 수 있습니다.
                </p>
              </MessageScrollerItem>
              <MessageScrollerItem scrollAnchor>
                <p className="rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground">
                  마지막 메시지 · 아래로 이동할 수 있습니다.
                </p>
              </MessageScrollerItem>
            </MessageScrollerContent>
          </MessageScrollerViewport>
        </MessageScroller>
      </MessageScrollerProvider>
    </Specimen>
  )
}

export const PopoverExample = () => {
  return (
    <Specimen
      name="popover"
      title="Popover"
      description="A compact non-modal surface opens from a labelled trigger."
    >
      <Popover>
        <PopoverTrigger render={<Button variant="outline" />}>
          토큰 정보
        </PopoverTrigger>
        <PopoverContent>
          <PopoverTitle>포커스 링</PopoverTitle>
          <PopoverDescription className="mt-1">
            --border-primary-focused가 활성 모드에 맞게 적용됩니다.
          </PopoverDescription>
        </PopoverContent>
      </Popover>
    </Specimen>
  )
}

export const ProgressExample = () => {
  return (
    <Specimen
      name="progress"
      title="Progress"
      description="Progress exposes its current numeric value to assistive technology."
    >
      <div className="grid gap-2">
        <div className="flex items-center justify-between text-sm">
          <span>토큰 검사</span>
          <span className="font-mono text-muted-foreground">72%</span>
        </div>
        <Progress aria-label="토큰 검사 진행률" value={72} />
      </div>
    </Specimen>
  )
}

export const SheetExample = () => {
  return (
    <Specimen
      name="sheet"
      title="Sheet"
      description="An edge-aligned modal surface remains dismissible and keyboard operable."
    >
      <Sheet>
        <SheetTrigger render={<Button variant="outline" />}>
          오른쪽에서 열기
        </SheetTrigger>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>토큰 세부 정보</SheetTitle>
            <SheetDescription>
              시맨틱 변수 이름과 기본 사용 원칙을 확인합니다.
            </SheetDescription>
          </SheetHeader>
          <SheetFooter>
            <SheetClose render={<Button variant="outline" />}>닫기</SheetClose>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </Specimen>
  )
}

export const SkeletonExample = () => {
  return (
    <Specimen
      name="skeleton"
      title="Skeleton"
      description="A loading placeholder uses a muted KDS surface instead of literal colors."
    >
      <div aria-label="콘텐츠 불러오는 중" role="status" className="grid gap-3">
        <div className="flex items-center gap-3">
          <Skeleton className="size-10 rounded-full" />
          <div className="grid flex-1 gap-2">
            <Skeleton className="h-3 w-1/3" />
            <Skeleton className="h-3 w-2/3" />
          </div>
        </div>
        <Skeleton className="h-16 w-full rounded-lg" />
      </div>
    </Specimen>
  )
}

export const SpinnerExample = () => {
  return (
    <Specimen
      name="spinner"
      title="Spinner"
      description="The ongoing state has a text alternative and status role."
    >
      <div className="flex items-center gap-3">
        <Spinner aria-hidden="true" />
        <span role="status" className="text-sm text-muted-foreground">
          토큰을 불러오는 중
        </span>
      </div>
    </Specimen>
  )
}

export const ToastExample = () => {
  return (
    <Specimen
      name="toast"
      title="Toast"
      description="A success notification appears after a real user action."
    >
      <ToastDemo />
    </Specimen>
  )
}

export const TooltipExample = () => {
  return (
    <Specimen
      name="tooltip"
      title="Tooltip"
      description="A short description is available on hover and keyboard focus."
    >
      <Tooltip>
        <TooltipTrigger
          render={<Button aria-label="도움말" size="icon" variant="outline" />}
        >
          <CircleHelp aria-hidden="true" />
        </TooltipTrigger>
        <TooltipContent>포커스 링은 KDS 토큰을 사용합니다.</TooltipContent>
      </Tooltip>
    </Specimen>
  )
}
