import MindmapClient from '@/components/books/mindmap/MindmapClient'

type RouteParams = {
  courseId: string
  bookId: string
}

export const dynamic = 'force-dynamic'
export const revalidate = 0
export const fetchCache = 'force-no-store'

export default async function BookDetailMindmapPage({
  params
}: {
  params: Promise<RouteParams> | RouteParams
}) {
  const resolvedParams = params instanceof Promise ? await params : params
  const { courseId, bookId } = resolvedParams

  if (!courseId || !bookId) {
    return null
  }

  return (
    <MindmapClient
      courseId={courseId}
      bookId={bookId}
    />
  )
}
