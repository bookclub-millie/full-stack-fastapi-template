import { useSuspenseQuery } from '@tanstack/react-query'
import { createFileRoute, redirect } from '@tanstack/react-router'
import { Suspense } from 'react'

import { type UserPublic, UsersService } from '@/client'
import AddUser from '@/components/admin/add-user'
import { columns, type UserTableData } from '@/components/admin/columns'
import { DataTable } from '@/components/common/data-table'
import PendingUsers from '@/components/pending/pending-users'
import useAuth from '@/hooks/use-auth'

const getUsersQueryOptions = () => {
  return {
    queryFn: async () =>
      (await UsersService.readUsers({ query: { skip: 0, limit: 100 } })).data,
    queryKey: ['users']
  }
}

const UsersTableContent = () => {
  const { user: currentUser } = useAuth()
  const { data: users } = useSuspenseQuery(getUsersQueryOptions())

  const tableData: UserTableData[] = users.data.map((user: UserPublic) => ({
    ...user,
    isCurrentUser: currentUser?.id === user.id
  }))

  return <DataTable columns={columns} data={tableData} />
}

const UsersTable = () => {
  return (
    <Suspense fallback={<PendingUsers />}>
      <UsersTableContent />
    </Suspense>
  )
}

const Admin = () => {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Users</h1>
          <p className="text-muted-foreground">
            Manage user accounts and permissions
          </p>
        </div>
        <AddUser />
      </div>
      <UsersTable />
    </div>
  )
}
export const Route = createFileRoute('/_layout/admin')({
  component: Admin,
  beforeLoad: async () => {
    const { data: user } = await UsersService.readUserMe()
    if (!user.is_superuser) {
      throw redirect({
        to: '/'
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: 'Admin - FastAPI Template'
      }
    ]
  })
})
