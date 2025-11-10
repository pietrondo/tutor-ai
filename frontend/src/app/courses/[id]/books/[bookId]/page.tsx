import BookDetailClient from '@/components/books/BookDetailClient'

export const dynamic = 'force-dynamic'
export const revalidate = 0
export const fetchCache = 'force-no-store'

export default async function CourseBookPage({
  params
}: {
  params: Promise<{
    id: string
    bookId: string
  }>
}) {
  const resolvedParams = await params
  const courseId = resolvedParams.id
  const bookId = resolvedParams.bookId

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
