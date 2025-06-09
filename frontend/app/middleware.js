import { withAuth } from 'next-auth/middleware'

export default withAuth(
  function middleware(req) {
    // 這裡可以加入額外的邏輯
  },
  {
    callbacks: {
      authorized: ({ token }) => !!token
    },
  }
)

export const config = {
  matcher: ['/dashboard/:path*', '/profile/:path*'] // 需要登入的路由
}