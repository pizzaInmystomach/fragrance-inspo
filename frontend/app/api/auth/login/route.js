import { loginUser } from "@/queries/user/userAuth";
import { NextResponse } from "next/server";

// 用戶登入
export async function POST(req) {
    try {
        const data = await req.json();

        // 獲取客戶端IP
        const clientIP = req.headers.get('x-forwarded-for') || 
                        req.headers.get('x-real-ip') || 
                        req.ip || 
                        'unknown';

        const loginData = {
            email: data.email,
            password: data.password,
            clientIP: clientIP
        };

        const result = await loginUser(loginData);

        if (result.status === 200) {
            // 創建 Response 並設定 HttpOnly cookie
            const response = NextResponse.json({ 
                success: true,
                message: result.message,
                token: result.token,
                user: result.user
            }, { status: 200 });

            // 設定 HttpOnly cookie
            response.cookies.set('auth_token', result.token, {
                httpOnly: true,      // 防止 XSS 攻擊
                secure: process.env.NODE_ENV === 'production', // HTTPS only in production
                sameSite: 'lax',  // CSRF 保護
                maxAge: 24 * 60 * 60, // 24 小時(秒)
                path: '/'            // cookie 適用於整個網站
            });

            return response;
        } else {
            return NextResponse.json({ 
                success: false,
                message: result.message 
            }, { status: result.status });
        }

    } catch (error) {
        console.error('Error during login:', error);
        return NextResponse.json({ 
            success: false,
            message: error.message || 'Login failed'
        }, { status: 500 });
    }
}