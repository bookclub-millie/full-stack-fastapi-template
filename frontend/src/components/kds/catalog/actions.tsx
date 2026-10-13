import { ArrowUpRight, Bold, Check, Italic, Link2, Star } from "lucide-react"

import { Specimen } from "./specimen"
import { Avatar, AvatarFallback, AvatarGroup } from "@kds/ui/components/avatar"
import { Badge } from "@kds/ui/components/badge"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@kds/ui/components/breadcrumb"
import { Button } from "@kds/ui/components/button"
import {
  ButtonGroup,
  ButtonGroupSeparator,
  ButtonGroupText,
} from "@kds/ui/components/button-group"
import { Kbd, KbdGroup } from "@kds/ui/components/kbd"
import { Marker, MarkerContent, MarkerIcon } from "@kds/ui/components/marker"
import { Toggle } from "@kds/ui/components/toggle"
import { ToggleGroup, ToggleGroupItem } from "@kds/ui/components/toggle-group"

export function ActionSpecimens() {
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <Specimen
        name="button"
        title="Button"
        description="Action hierarchy, sizes, icon placement, and disabled state."
      >
        <div className="flex flex-wrap items-center gap-2">
          <Button>기본 액션</Button>
          <Button variant="outline">보조 액션</Button>
          <Button variant="ghost">텍스트 액션</Button>
          <Button disabled variant="outline">
            비활성
          </Button>
          <Button aria-label="새 창으로 열기" size="icon" variant="secondary">
            <ArrowUpRight aria-hidden="true" />
          </Button>
        </div>
      </Specimen>

      <Specimen
        name="badge"
        title="Badge"
        description="Compact semantic labels using the active KDS mode."
      >
        <div className="flex flex-wrap items-center gap-2">
          <Badge>기본</Badge>
          <Badge variant="secondary">보조</Badge>
          <Badge variant="outline">초안</Badge>
          <Badge variant="destructive">확인 필요</Badge>
        </div>
      </Specimen>

      <Specimen
        name="avatar"
        title="Avatar"
        description="Initials remain legible when no profile image is available."
      >
        <AvatarGroup>
          <Avatar aria-label="홍길동" size="lg">
            <AvatarFallback>홍</AvatarFallback>
          </Avatar>
          <Avatar aria-label="김하나" size="lg">
            <AvatarFallback>김</AvatarFallback>
          </Avatar>
          <Avatar aria-label="이둘" size="lg">
            <AvatarFallback>이</AvatarFallback>
          </Avatar>
        </AvatarGroup>
      </Specimen>

      <Specimen
        name="breadcrumb"
        title="Breadcrumb"
        description="A short hierarchy with the current page announced semantically."
      >
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href="#top">갤러리</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbLink href="#actions">컴포넌트</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>버튼</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </Specimen>

      <Specimen
        name="button-group"
        title="Button Group"
        description="Related commands stay visually and semantically grouped."
      >
        <ButtonGroup aria-label="텍스트 서식">
          <ButtonGroupText>서식</ButtonGroupText>
          <ButtonGroupSeparator />
          <Button aria-label="굵게" size="icon" variant="outline">
            <Bold aria-hidden="true" />
          </Button>
          <Button aria-label="기울임" size="icon" variant="outline">
            <Italic aria-hidden="true" />
          </Button>
          <Button aria-label="링크" size="icon" variant="outline">
            <Link2 aria-hidden="true" />
          </Button>
        </ButtonGroup>
      </Specimen>

      <Specimen
        name="kbd"
        title="Kbd"
        description="Keyboard shortcuts use a readable, compact keycap treatment."
      >
        <div className="flex items-center gap-3 text-sm">
          <KbdGroup aria-label="검색 단축키">
            <Kbd>⌘</Kbd>
            <Kbd>K</Kbd>
          </KbdGroup>
          <span className="text-muted-foreground">검색 열기</span>
        </div>
      </Specimen>

      <Specimen
        name="marker"
        title="Marker"
        description="A small status marker with a text equivalent."
      >
        <Marker>
          <MarkerIcon>
            <Check aria-hidden="true" />
          </MarkerIcon>
          <MarkerContent>토큰 연결됨</MarkerContent>
        </Marker>
      </Specimen>

      <Specimen
        name="toggle"
        title="Toggle"
        description="A keyboard-operable pressed state for a single formatting option."
      >
        <Toggle aria-label="즐겨찾기" defaultPressed>
          <Star aria-hidden="true" />
          <span>즐겨찾기</span>
        </Toggle>
      </Specimen>

      <Specimen
        name="toggle-group"
        title="Toggle Group"
        description="Multiple pressed values can be independently selected."
      >
        <ToggleGroup
          aria-label="텍스트 서식 옵션"
          defaultValue={["bold"]}
          multiple
        >
          <ToggleGroupItem aria-label="굵게" value="bold">
            <Bold aria-hidden="true" />
          </ToggleGroupItem>
          <ToggleGroupItem aria-label="기울임" value="italic">
            <Italic aria-hidden="true" />
          </ToggleGroupItem>
          <ToggleGroupItem aria-label="링크" value="link">
            <Link2 aria-hidden="true" />
          </ToggleGroupItem>
        </ToggleGroup>
      </Specimen>
    </div>
  )
}
