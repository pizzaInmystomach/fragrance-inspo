// app/api/chat/route.js

import { NextResponse } from 'next/server';
import { aiChatCompletion } from '@/lib/ai-service';
import { getFragrancesByAttributes } from '@/lib/fragrance-service';

export async function POST(request) {
    try {
        const data = await request.json();
        const { messages, userId } = data;
        
        if (!messages || !Array.isArray(messages)) {
        return NextResponse.json(
            { error: 'Invalid message format' },
            { status: 400 }
        );
        }

        // ① 把歷史 messages 送進 ai-service.js → Python AI
        const aiResponse = await aiChatCompletion(messages);
        
        // ② 從 AI 回傳的 analysis 拆出 personality / notes…
        const { 
        personality, 
        notes, 
        mood, 
        occasion, 
        specificRequest,
        needsRecommendation
        } = aiResponse.analysis;

        // ③ 只有在 AI 判斷需要推薦時，才呼叫 DB-service
        let fragrances = [];
        
        if (needsRecommendation) {
            fragrances = await getFragrancesByAttributes({
                personality,
                notes,
                mood,
                occasion
            });
        }
        
        // ④ 把 AI 回覆的文字、推薦清單、analysis 打包回前端
        return NextResponse.json({
        message: aiResponse.message,
        fragrances: fragrances,
        analysis: aiResponse.analysis
        });
    } catch (error) {
        console.error('Chat API error:', error);
        return NextResponse.json(
        { error: 'Failed to process request' },
        { status: 500 }
        );
    }
}