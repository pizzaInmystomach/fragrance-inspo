// app/api/auth/verify/route.js
import { verifyUserToken } from "@/queries/user/userAuth";
import { NextResponse } from "next/server";

// 驗證用戶 token
export async function GET(req) {
    try {
        // 優先從 cookie 取得 token
        const cookieToken = req.cookies.get('auth_token')?.value;
        
        // 備用: 從 Authorization header 取得 token
        const authHeader = req.headers.get('authorization');
        const headerToken = authHeader?.replace('Bearer ', '');
        
        const token = cookieToken || headerToken;
        
        console.log('API Verify - Token check:', {
            hasCookieToken: !!cookieToken,
            hasHeaderToken: !!headerToken,
            finalToken: !!token
        });
        
        if (!token) {
            console.log('API Verify - No token provided');
            return NextResponse.json({ 
                status: 401,
                success: false,
                message: 'No token provided' 
            }, { status: 401 });
        }

        const result = await verifyUserToken(token);
        console.log('API Verify - Result:', result);

        if (result.status === 200) {
            return NextResponse.json({
                status: 200,  // 重要：添加 status 字段給 middleware 使用
                success: true,
                message: result.message,
                user: result.user
            }, { status: 200 });
        } else {
            return NextResponse.json({
                status: result.status,  // 重要：添加 status 字段
                success: false,
                message: result.message
            }, { status: result.status });
        }

    } catch (error) {
        console.error('Error during token verification:', error);
        return NextResponse.json({ 
            status: 500,  // 重要：添加 status 字段
            success: false,
            message: error.message || 'Token verification failed'
        }, { status: 500 });
    }
}