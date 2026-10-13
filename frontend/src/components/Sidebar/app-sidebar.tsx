import { Briefcase, Home, Users } from 'lucide-react'

import { SidebarAppearance } from '@/components/Common/appearance'
import { Logo } from '@/components/Common/logo'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader
} from '@/components/ui/sidebar'
import useAuth from '@/hooks/use-auth'
import { type Item, Main } from './main'
import { User } from './user'

const baseItems: Item[] = [
  { icon: Home, title: 'Dashboard', path: '/' },
  { icon: Briefcase, title: 'Items', path: '/items' }
]

const AppSidebar = () => {
  const { user: currentUser } = useAuth()

  const items = currentUser?.is_superuser
    ? [...baseItems, { icon: Users, title: 'Admin', path: '/admin' }]
    : baseItems

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        <Logo variant="responsive" />
      </SidebarHeader>
      <SidebarContent>
        <Main items={items} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarAppearance />
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}

export default AppSidebar
