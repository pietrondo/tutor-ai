import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'

export default function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  console.log(`[middleware] incoming ${pathname}`)

  // Fix per le mindmap: reindirizza solo le route /courses/*/books/*/mindmap
  const mindmapMatch = pathname.match(/^\/courses\/([^/]+)\/books\/([^/]+)\/mindmap$/)
  if (mindmapMatch) {
    const [, courseId, bookId] = mindmapMatch
    const targetPath = `/book-detail/${courseId}/${bookId}/mindmap`
    console.log(`[middleware] rewriting mindmap ${pathname} -> ${targetPath}`)

    const rewriteUrl = request.nextUrl.clone()
    rewriteUrl.pathname = targetPath
    return NextResponse.rewrite(rewriteUrl)
  }

  // NOTA: NON toccare le altre route /courses/*/books/*
  // devono funzionare normalmente senza rewriting

  return NextResponse.next()
}

export const config = {
  matcher: ['/courses/:path*/books/:path*/mindmap']
}