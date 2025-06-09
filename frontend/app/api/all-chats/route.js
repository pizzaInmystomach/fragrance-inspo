import { getAllChats } from "@/queries/chat/findAllChats";
import { NextResponse } from "next/server";
import { v4 as uuidv4 } from 'uuid';

export async function GET(req) {
    const { searchParams } = new URL(req.url);
    const userID = searchParams.get("userID");

    const findAllChats = await getAllChats(userID);

    if (findAllChats.status === 200) {
        return new Response(JSON.stringify({ message: 'Found the user\'s chats history', result: findAllChats.result }), {
            status: 200,
            headers:{
                'Content-Type': 'application/json',
            },
        })
    } else if (findAllChats.status === 400) {
        return new Response(JSON.stringify({ message: 'User not found' }), {
            status: 400,
            headers:{
                'Content-Type': 'application/json',
            },
        })
    } else {
        return new Response(JSON.stringify({ message: 'Server error' }), {
            status: 500,
            headers:{
                'Content-Type': 'application/json',
            },
        })
    }
}