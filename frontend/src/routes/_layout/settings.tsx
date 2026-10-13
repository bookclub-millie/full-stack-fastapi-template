import { createFileRoute } from '@tanstack/react-router'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import ChangePassword from '@/components/user-settings/change-password'
import DeleteAccount from '@/components/user-settings/delete-account'
import UserInformation from '@/components/user-settings/user-information'
import useAuth from '@/hooks/use-auth'

const tabsConfig = [
  { value: 'my-profile', title: 'My profile', component: UserInformation },
  { value: 'password', title: 'Password', component: ChangePassword },
  { value: 'danger-zone', title: 'Danger zone', component: DeleteAccount }
]

const UserSettings = () => {
  const { user: currentUser } = useAuth()
  const finalTabs = currentUser?.is_superuser
    ? tabsConfig.slice(0, 3)
    : tabsConfig

  if (!currentUser) {
    return null
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">User Settings</h1>
        <p className="text-muted-foreground">
          Manage your account settings and preferences
        </p>
      </div>

      <Tabs defaultValue="my-profile">
        <TabsList>
          {finalTabs.map(tab => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.title}
            </TabsTrigger>
          ))}
        </TabsList>
        {finalTabs.map(tab => (
          <TabsContent key={tab.value} value={tab.value}>
            <tab.component />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
export const Route = createFileRoute('/_layout/settings')({
  component: UserSettings,
  head: () => ({
    meta: [
      {
        title: 'Settings - FastAPI Template'
      }
    ]
  })
})
