import { Button } from "@kds/ui/components/button"
import { Toaster, toast } from "@kds/ui/components/toast"

export function ToastDemo() {
  return (
    <Toaster>
      <Button
        onClick={() =>
          toast.add({
            title: "테마 미리보기",
            description: "KDS 토큰 모드가 적용되었습니다.",
            type: "success",
          })
        }
        variant="outline"
      >
        알림 표시
      </Button>
    </Toaster>
  )
}
