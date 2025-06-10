// app/api/chat/send-message/route.js
import { userSendMessage } from "@/queries/chat/userSendMessage";
import { aiChatCompletion } from '@/lib/ai-service';
import { getFragrancesByAttributes } from '@/lib/fragrance-service';
import { NextResponse } from "next/server";

console.log('AI_SERVICE_URL=>', process.env.AI_SERVICE_URL);
console.log('AI_SERVICE_API_KEY=>', process.env.AI_SERVICE_API_KEY);

export async function POST(req) {
    try {
        const data = await req.json();
        console.log('Request data:', data);

        // 檢查是否有 name 參數
        const { name } = data;
        
        let aiData = null;
        
        if (name && typeof name === 'string') {
            console.log('name:', name);
            
            try {
                // 使用 AI 服務進行分析和推薦
                const { character, recommendations } = await aiChatCompletion([
                    { role: 'user', content: name.trim() },
                ]);

                let fragrances = recommendations;

                // 如果 AI 沒有提供推薦，使用資料庫 fallback
                if (!fragrances.length) {
                    fragrances = await getFragrancesByAttributes({
                        personality: character.personality,
                        notes: character.notes,
                    });
                }

                aiData = {
                    character,
                    recommendations: fragrances
                };
            } catch (aiError) {
                console.error('AI processing error:', aiError);
            }
        }

        // 傳送訊息至後端 包含 AI 推薦功能
        const result = await userSendMessage(data);

        return new Response(JSON.stringify({
            message: result.message || 'Message sent',
            result,
            // 如果有 AI 回覆相關資料，一併回傳
            ...(result.character && { character: result.character }),
            ...(result.recommendations && { recommendations: result.recommendations }),
            ...(result.botReply && { botReply: result.botReply }),
            // 新增的 AI 資料
            ...(aiData && aiData)
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