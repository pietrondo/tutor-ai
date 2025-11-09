import BookDetailClient from '@/components/books/BookDetailClient'

type RouteParams = {
  courseId: string
  bookId: string
}

export const dynamic = 'force-dynamic'
export const revalidate = 0
export const fetchCache = 'force-no-store'

export default async function BookDetailPage({ params }: { params: Promise<RouteParams> | RouteParams }) {
  const resolvedParams = params instanceof Promise ? await params : params
  const { courseId, bookId } = resolvedParams

  if (!courseId || !bookId) {
    return null
  }

  return (
    <BookDetailClient
      courseId={courseId}
      bookId={bookId}
    />
  )
}
