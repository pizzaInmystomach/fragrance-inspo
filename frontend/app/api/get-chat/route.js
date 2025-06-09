// app/api/get-chat/route.js

import { getChatByUserAndChatID } from '@/queries/chat/findOneChat';

export async function GET(req) {
    const { searchParams } = new URL(req.url);
    const userID = searchParams.get("userID");
    const chatID = searchParams.get("chatID");

    if (!userID || !chatID) {
        return new Response(JSON.stringify({ error: 'Missing userID or chatID' }), {
            status: 400,
            headers: { 'Content-Type': 'application/json' },
        });
    }

    try {
        const result = await getChatByUserAndChatID({ userID, chatID });

        if (result.status === 200) {
            return new Response(JSON.stringify({ status: result.status, message: 'Chat found', chat: result.chat }), {
                status: 200,
                headers: { 'Content-Type': 'application/json' },
            });
        } else {
            return new Response(JSON.stringify({ error: result.error }), {
                status: result.status,
                headers: { 'Content-Type': 'application/json' },
            });
        }
    } catch (error) {
        console.error("Error fetching chat:", error);
        return new Response(JSON.stringify({ error: 'Internal Server Error' }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' },
        });
    }
}
