import { NextResponse } from 'next/server';
import { deleteChat } from '@/queries/chat/deleteChat';

export async function DELETE(request) {
  try {
    const { searchParams } = new URL(request.url);
    const userID = searchParams.get('userID');
    const chatID = searchParams.get('chatID');

    if (!userID || !chatID) {
      return NextResponse.json(
        { message: '缺少 userID 或 chatID' },
        { status: 400 }
      );
    }

    const result = await deleteChat({ userID, chatID });

    return NextResponse.json(result, { status: result.status });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { message: '刪除聊天過程中發生錯誤' },
      { status: 500 }
    );
  }
}
