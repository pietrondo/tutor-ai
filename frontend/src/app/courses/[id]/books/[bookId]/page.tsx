import BookDetailClient from '@/components/books/BookDetailClient'

interface CourseBookPageProps {
  params: {
    id: string
    bookId: string
  }
}

export const dynamic = 'force-dynamic'
export const revalidate = 0
export const fetchCache = 'force-no-store'

export default function CourseBookPage({ params }: CourseBookPageProps) {
  const courseId = params.id
  const bookId = params.bookId

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
