import clientPromise from "@/lib/mongodb";
import { ObjectId } from "mongodb";

export const deleteChat = async (data) => {
    const client = await clientPromise;
    const db = client.db('fragrance_inspo_app_db');
    const user_collection = db.collection('users');
    const chat_collection = db.collection('users_chat');

    const { userID, chatID } = data;

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

        // 根據 userID 和 chatID 刪除聊天記錄
        const result = await chat_collection.deleteOne({
            user: userObjectId,
            chatId: chatID
        });

        if (result.deletedCount === 0) {
            return {
                status: 404,
                message: '找不到對應的聊天紀錄'
            };
        }

        return {
            status: 200,
            message: '聊天已成功刪除'
        };
    } catch (error) {
        console.error('Error deleting chat:', error);
        return {
            status: 500,
            message: error.message || 'Failed to delete chat'
        };
    }
};
