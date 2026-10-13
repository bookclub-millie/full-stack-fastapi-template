import { Home, Layers, Search, Settings2 } from "lucide-react"

import { Specimen } from "./specimen"
import { Button } from "@kds/ui/components/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@kds/ui/components/command"
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuTrigger,
} from "@kds/ui/components/context-menu"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuLabel,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
} from "@kds/ui/components/dropdown-menu"
import {
  Menubar,
  MenubarContent,
  MenubarItem,
  MenubarMenu,
  MenubarSeparator,
  MenubarShortcut,
  MenubarTrigger,
} from "@kds/ui/components/menubar"
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
} from "@kds/ui/components/navigation-menu"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@kds/ui/components/sidebar"

export function NavigationSpecimens() {
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <Specimen
        name="command"
        title="Command"
        description="Type to filter actions, then move with arrow keys and select with Enter."
      >
        <Command className="rounded-lg border border-border">
          <CommandInput aria-label="명령 검색" placeholder="명령 검색…" />
          <CommandList>
            <CommandEmpty>일치하는 명령이 없습니다.</CommandEmpty>
            <CommandGroup heading="이동">
              <CommandItem value="components">
                <Layers aria-hidden="true" />
                컴포넌트 카탈로그
              </CommandItem>
              <CommandItem value="tokens">
                <Search aria-hidden="true" />
                토큰 찾기
              </CommandItem>
              <CommandItem value="settings">
                <Settings2 aria-hidden="true" />
                설정
              </CommandItem>
            </CommandGroup>
          </CommandList>
        </Command>
      </Specimen>

      <Specimen
        name="context-menu"
        title="Context Menu"
        description="Right-click the focusable target, or use Shift+F10 to open its menu."
      >
        <ContextMenu>
          <ContextMenuTrigger
            className="flex min-h-20 items-center justify-center rounded-lg border border-dashed border-border px-4 text-sm text-muted-foreground focus-visible:outline-2 focus-visible:outline-ring"
            tabIndex={0}
          >
            오른쪽 클릭 또는 Shift+F10
          </ContextMenuTrigger>
          <ContextMenuContent>
            <ContextMenuItem>복사</ContextMenuItem>
            <ContextMenuItem>링크 열기</ContextMenuItem>
            <ContextMenuSeparator />
            <ContextMenuItem disabled>비활성 항목</ContextMenuItem>
          </ContextMenuContent>
        </ContextMenu>
      </Specimen>

      <Specimen
        name="dropdown-menu"
        title="Dropdown Menu"
        description="A labelled trigger opens a menu with enabled and disabled actions."
      >
        <DropdownMenu>
          <DropdownMenuTrigger render={<Button variant="outline" />}>
            보기 옵션
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            <DropdownMenuGroup>
              <DropdownMenuLabel>표시</DropdownMenuLabel>
              <DropdownMenuItem>
                밀도 조정
                <DropdownMenuShortcut>⌘ D</DropdownMenuShortcut>
              </DropdownMenuItem>
              <DropdownMenuItem>정렬 기준</DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuItem disabled>저장할 설정 없음</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </Specimen>

      <Specimen
        name="menubar"
        title="Menubar"
        description="Top-level menus support keyboard navigation between commands."
      >
        <Menubar>
          <MenubarMenu>
            <MenubarTrigger>파일</MenubarTrigger>
            <MenubarContent>
              <MenubarItem>
                새 보기
                <MenubarShortcut>⌘ N</MenubarShortcut>
              </MenubarItem>
              <MenubarItem>내보내기</MenubarItem>
              <MenubarSeparator />
              <MenubarItem disabled>저장</MenubarItem>
            </MenubarContent>
          </MenubarMenu>
          <MenubarMenu>
            <MenubarTrigger>편집</MenubarTrigger>
            <MenubarContent>
              <MenubarItem>복사</MenubarItem>
              <MenubarItem>붙여넣기</MenubarItem>
            </MenubarContent>
          </MenubarMenu>
        </Menubar>
      </Specimen>

      <Specimen
        name="navigation-menu"
        title="Navigation Menu"
        description="A simple nested navigation set preserves links as real anchors."
      >
        <NavigationMenu>
          <NavigationMenuList>
            <NavigationMenuItem>
              <NavigationMenuTrigger>라이브러리</NavigationMenuTrigger>
              <NavigationMenuContent>
                <div className="grid w-56 gap-1 p-2">
                  <NavigationMenuLink href="#actions">
                    액션 컴포넌트
                  </NavigationMenuLink>
                  <NavigationMenuLink href="#forms">
                    입력 컴포넌트
                  </NavigationMenuLink>
                  <NavigationMenuLink href="#surfaces">
                    표면 컴포넌트
                  </NavigationMenuLink>
                </div>
              </NavigationMenuContent>
            </NavigationMenuItem>
          </NavigationMenuList>
        </NavigationMenu>
      </Specimen>

      <Specimen
        name="sidebar"
        title="Sidebar"
        description="The local side rail has a labelled collapse control and active item."
      >
        <SidebarProvider className="min-h-64 overflow-hidden rounded-xl border border-border">
          <Sidebar collapsible="icon" className="relative top-0 h-64">
            <SidebarHeader>
              <SidebarTrigger aria-label="사이드바 접기 또는 펼치기" />
            </SidebarHeader>
            <SidebarContent>
              <SidebarGroup>
                <SidebarGroupLabel>카탈로그</SidebarGroupLabel>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton isActive tooltip="홈">
                      <Home aria-hidden="true" />
                      <span>홈</span>
                    </SidebarMenuButton>
                    <SidebarMenuBadge>12</SidebarMenuBadge>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton tooltip="컴포넌트">
                      <Layers aria-hidden="true" />
                      <span>컴포넌트</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroup>
            </SidebarContent>
            <SidebarFooter>
              <p className="truncate px-2 text-xs text-muted-foreground">
                KDS 2.0
              </p>
            </SidebarFooter>
          </Sidebar>
        </SidebarProvider>
      </Specimen>
    </div>
  )
}
