import BookDetailClient from '@/components/books/BookDetailClient'

interface BookDetailPageProps {
  params: {
    courseId: string
    bookId: string
  }
}

export const dynamic = 'force-dynamic'
export const revalidate = 0
export const fetchCache = 'force-no-store'

export default function BookDetailPage({ params }: BookDetailPageProps) {
  const { courseId, bookId } = params

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
