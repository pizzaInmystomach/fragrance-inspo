// app/api/chat/send-message/route.js
import { userSendMessage } from "@/queries/chat/userSendMessage";
import { NextResponse } from "next/server";

export async function POST(req) {
    try {
        const data = await req.json();

        // 傳送訊息至後端，現在包含 AI 推薦功能
        const result = await userSendMessage(data);

        return new Response(JSON.stringify({
            message: result.message || 'Message sent',
            result,
            // 如果有 AI 回覆相關資料，一併回傳
            ...(result.character && { character: result.character }),
            ...(result.recommendations && { recommendations: result.recommendations }),
            ...(result.botReply && { botReply: result.botReply })
        }), {
            status: result.status,
            headers: {
                'Content-Type': 'application/json',
            },
        });

    } catch (error) {
        console.error('Error sending message:', error);
        return new Response(JSON.stringify({
            message: error.message || 'Failed to send message',
        }), {
            status: 400,
            headers: {
                'Content-Type': 'application/json',
            },
        });
    }
}