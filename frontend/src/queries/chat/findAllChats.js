import clientPromise from "@/lib/mongodb";
import { ObjectId } from "mongodb";
import Chat from "@/models/Chat";

export const getAllChats = async (userID) => {
    const client = await clientPromise;
    const db = client.db('fragrance_inspo_app_db');
    const user_collection = db.collection('users');
    const chat_collection = db.collection('users_chat');

    // 找到是否有該使用者id
    // 找不到則返回錯誤
    const userIDObjectId = new ObjectId(userID);
    const existingUser = await user_collection.findOne({ '_id': userIDObjectId });
    //如果使用者存在則可以繼續建立新聊天
    if (!existingUser) {
        return {
            status: 400,
            error: 'User not found'
        };
    } else {
        // 根據使用者ID找到所有聊天
        const result = await chat_collection.find({ user: userIDObjectId }).toArray();
        
        return {
            status: 200,
            message: 'User found',
            result
        };
    }
}