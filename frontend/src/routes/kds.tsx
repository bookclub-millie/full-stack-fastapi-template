import { TooltipProvider } from "@kds/ui/components/tooltip"
import { createFileRoute } from "@tanstack/react-router"
import KdsGallery from "@/components/kds/gallery"

export const Route = createFileRoute("/kds")({
  component: KdsPage,
  head: () => ({
    meta: [
      { title: "KDS 2.0 · Component Gallery" },
      {
        name: "description",
        content: "KDS 2.0 디자인 토큰을 적용한 컴포넌트 미리보기.",
      },
    ],
  }),
})

function KdsPage() {
  return (
    <TooltipProvider>
      <div lang="ko">
        <KdsGallery />
      </div>
    </TooltipProvider>
  )
}
