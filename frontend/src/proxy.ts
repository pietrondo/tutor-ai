import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'

export default function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl
  console.log(`[proxy] incoming ${pathname}`)

  const match = pathname.match(/^\/courses\/([^/]+)\/books\/([^/]+)(\/.*)?$/)
  if (match) {
    const [, courseId, bookId, rest] = match
    const targetPath = `/book-detail/${courseId}/${bookId}${rest ?? ''}`
    console.log(`[proxy] rewriting ${pathname} -> ${targetPath}`)

    const rewriteUrl = request.nextUrl.clone()
    rewriteUrl.pathname = targetPath
    return NextResponse.rewrite(rewriteUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/courses/:path*']
}
