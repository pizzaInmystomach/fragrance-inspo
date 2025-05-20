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

        // Get AI response to understand user intent
        const aiResponse = await aiChatCompletion(messages);
        
        // Extract fragrance preferences from AI analysis
        const { 
        personality, 
        notes, 
        mood, 
        occasion, 
        specificRequest,
        needsRecommendation
        } = aiResponse.analysis;

        let fragrances = [];
        
        // Only fetch fragrance recommendations if the AI determined we need them
        if (needsRecommendation) {
        // Get fragrances from database based on AI analysis
        fragrances = await getFragrancesByAttributes({
            personality,
            notes,
            mood,
            occasion
        });
        }
        
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