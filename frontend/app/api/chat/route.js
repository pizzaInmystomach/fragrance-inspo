// app/api/chat/route.js

console.log('AI_SERVICE_URL=>', process.env.AI_SERVICE_URL);
console.log('AI_SERVICE_API_KEY=>', process.env.AI_SERVICE_API_KEY);

import { NextResponse } from 'next/server';
import { aiChatCompletion } from '@/lib/ai-service';
import { getFragrancesByAttributes } from '@/lib/fragrance-service';

export async function POST(req) {
    try {
        const {name} = await req.json();
        console.log('name:', name);

        if (!name || typeof name !== 'string') {
          return NextResponse.json(
            { error: 'Name is required' },
            { status: 400}
          );
        }

        // build chat history from single name input
        const { character, recommendations } = await aiChatCompletion ([
          { role: 'user', content: name.trim() },
        ]);


        let fragrances = recommendations;

        if (!fragrances.length) {
            // 後端沒給清單，再 fallback 用 DB 做
            fragrances = await getFragrancesByAttributes({
                personality: character.personality,
                notes: character.notes,
            });
        }
        
        // 把 AI 回覆的文字、推薦清單、analysis 打包回前端
        return NextResponse.json({
            character,
            recommendations: fragrances
        });
    } catch (error) {
        console.error('Chat API error:', error);
        return NextResponse.json(
        { error: 'Failed to process request' },
        { status: 500 }
        );
    }
}