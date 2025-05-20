// app/api/history/route.js

import { NextResponse } from 'next/server';
import { 
    getChatHistory, 
    createChatSession, 
    saveChatMessage 
} from '@/lib/chat-service';

// Get history
export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get('userId');
    
    if (!userId) {
      return NextResponse.json(
        { error: 'User ID is required' },
        { status: 400 }
      );
    }
    
    const chatHistory = await getChatHistory(userId);
    return NextResponse.json({ chatHistory });
  } catch (error) {
    console.error('Chat history API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch chat history' },
      { status: 500 }
    );
  }
}

// Create a new chat session
export async function POST(request) {
  try {
    const data = await request.json();
    const { userId, title } = data;
    
    if (!userId) {
      return NextResponse.json(
        { error: 'User ID is required' },
        { status: 400 }
      );
    }
    
    const chatSession = await createChatSession(userId, title || 'New Chat');
    return NextResponse.json({ chatSession });
  } catch (error) {
    console.error('Create chat session API error:', error);
    return NextResponse.json(
      { error: 'Failed to create chat session' },
      { status: 500 }
    );
  }
}

// app/api/history/[sessionId]/route.js - would handle CRUD for specific chat sessions