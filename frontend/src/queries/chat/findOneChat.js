import clientPromise from "@/lib/mongodb";
import { ObjectId } from "mongodb";

export const getChatByUserAndChatID = async ({ userID, chatID }) => {
    const client = await clientPromise;
    const db = client.db('fragrance_inspo_app_db');
    const user_collection = db.collection('users');
    const chat_collection = db.collection('users_chat');

    // 驗證 user 是否存在
    const userIDObjectId = new ObjectId(userID);
    const existingUser = await user_collection.findOne({ _id: userIDObjectId });

    if (!existingUser) {
        return {
            status: 400,
            error: 'User not found',
        };
    }

    // 查找該 user 的指定 chatId
    const chat = await chat_collection.findOne({
        user: userIDObjectId,
        chatId: chatID,
    });

    if (!chat) {
        return {
            status: 404,
            error: 'Chat not found for this user',
        };
    }

    return {
        status: 200,
        message: 'Chat found',
        chat,
    };
};
