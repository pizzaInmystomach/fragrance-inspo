import { logoutUser } from "@/queries/user/userAuth";
import { NextResponse } from "next/server";

// 用戶登出
export async function POST(req) {
    try {
        const data = await req.json();
        const { userID } = data;

        // 創建 Response
        const response = NextResponse.json({ 
            success: true,
            message: 'Logout successful'
        }, { status: 200 });

        // 清除 auth_token cookie
        response.cookies.set('auth_token', '', {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
            maxAge: 0, // 立即過期
            path: '/'
        });

        // 如果有提供 userID，記錄登出
        if (userID) {
            const result = await logoutUser(userID);
            if (result.status !== 200) {
                console.warn('Logout recording failed:', result.message);
            }
        }

        return response;

    } catch (error) {
        console.error('Error during logout:', error);
        
        // 即使發生錯誤也要清除 cookie
        const response = NextResponse.json({ 
            success: true,
            message: 'Logout successful'
        }, { status: 200 });

        response.cookies.set('auth_token', '', {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
            maxAge: 0,
            path: '/'
        });

        return response;
    }
}