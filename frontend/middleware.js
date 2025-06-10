import { NextResponse } from "next/server";

export async function middleware(request) {
  const { pathname } = request.nextUrl;

  const cookieToken = request.cookies.get("auth_token")?.value;
  const headerToken = request.headers.get("authorization")?.replace("Bearer ", "");
  const authToken = cookieToken || headerToken;

  console.log('🔍 Middleware Debug:', {
    pathname,
    cookieToken: cookieToken ? 'EXISTS' : 'MISSING',
    headerToken: headerToken ? 'EXISTS' : 'MISSING',
    finalToken: authToken ? 'EXISTS' : 'MISSING'
  });

  const isProtectedPath = ["/chat", "/profile", "/dashboard"].some((path) =>
    pathname.startsWith(path)
  );

  const isAuthPage = pathname === "/login" || pathname === "/register";

  const verifyToken = async (token) => {
    try {
      const verifyUrl = new URL("/api/auth/verify", request.url);
      console.log('🔐 Verifying token at:', verifyUrl.toString());
      
      const response = await fetch(verifyUrl.toString(), {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      console.log('🔐 Verify response status:', response.status);

      if (!response.ok) {
        console.log('🔐 Verify failed - response not ok');
        return null;
      }

      const data = await response.json();
      console.log('🔐 Verify response data:', data);
      
      // 修改這裡：適應你的 API 返回格式
      if (data.success && data.user) {
        console.log('🔐 Token verified successfully for user:', data.user.email);
        return data.user;
      }

      console.log('🔐 Token verification failed - invalid response format');
      return null;
    } catch (error) {
      console.error("🚨 Token verification failed:", error);
      return null;
    }
  };

  // 🚫 已登入者訪問 login 或 register，導向 chat
  if (isAuthPage && authToken) {
    console.log('🔄 Auth page with token - verifying...');
    const user = await verifyToken(authToken);
    if (user) {
      console.log('🔄 Redirecting authenticated user to /chat');
      return NextResponse.redirect(new URL("/chat", request.url));
    } else {
      console.log('🔄 Token invalid - staying on auth page');
      // Token 無效，清除 cookie
      const response = NextResponse.next();
      response.cookies.delete('auth_token');
      return response;
    }
  }

  // 🔒 受保護頁面，需驗證
  if (isProtectedPath) {
    console.log('🔒 Protected path accessed');
    
    if (!authToken) {
      console.log('🔒 No token - redirecting to login');
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }

    const user = await verifyToken(authToken);
    if (!user) {
      console.log('🔒 Invalid token - redirecting to login');
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      const response = NextResponse.redirect(loginUrl);
      response.cookies.delete('auth_token');
      return response;
    }

    console.log('🔒 Token valid - allowing access');
    const requestHeaders = new Headers(request.headers);
    requestHeaders.set("x-user-id", user.id);
    requestHeaders.set("x-user-email", user.email);

    return NextResponse.next({
      request: { headers: requestHeaders },
    });
  }

  console.log('✅ Public path - no action needed');
  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}