import clientPromise from "@/lib/mongodb";
import { ObjectId } from "mongodb";

export const renameChat = async (data) => {
    const client = await clientPromise;
    const db = client.db('fragrance_inspo_app_db');
    const user_collection = db.collection('users');
    const chat_collection = db.collection('users_chat');

    const { userID, chatID, newTitle } = data;

    try {
        const userObjectId = new ObjectId(userID);

        // 驗證使用者是否存在
        const existingUser = await user_collection.findOne({ _id: userObjectId });
        if (!existingUser) {
            return {
                status: 400,
                message: '找不到該使用者'
            };
        }

        // 根據 userID 和 chatID 更新聊天標題
        const result = await chat_collection.updateOne(
            { user: userObjectId, chatId: chatID },
            { $set: { title: newTitle } }
        );

        if (result.matchedCount === 0) {
            return {
                status: 404,
                message: '找不到對應的聊天紀錄'
            };
        }

        return {
            status: 200,
            message: '聊天標題已更新',
            modifiedCount: result.modifiedCount
        };
    } catch (error) {
        console.error('Error renaming chat:', error);
        return {
            status: 500,
            message: error.message || 'Failed to rename chat'
        };
    }
};
