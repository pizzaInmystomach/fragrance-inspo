import clientPromise from "@/lib/mongodb";
import { v4 as uuidv4 } from 'uuid';
import Chat from "@/models/Chat";
import { ObjectId } from "mongodb";

export const createNewChat = async (data) => {
    const client = await clientPromise;
    const db = client.db('fragrance_inspo_app_db');
    const user_collection = db.collection('users');
    const chat_collection = db.collection('users_chat');

    const { userID } = data;
    const userObjectId = new ObjectId(userID);

    try {
        // 找到是否有該使用者id
        // 找到則繼續存資料
        // 找不到則回傳錯誤響應
        const existingUser = await user_collection.findOne({ _id: userObjectId });
        
        //如果使用者存在則可以繼續建立新聊天
        if (existingUser) {
            const title = 'New Chat';
            const createdAt = new Date();
            const chatId = uuidv4();
            const botMessage = 'Hi! Tell me the name of the person you want to find a fragrance for:'
            const timestamp = new Date().toISOString();
            const newChat = new Chat({
                user: userObjectId,
                chatId,
                // ID: userID,
                title,
                messages: [{
                    sender: 'bot',
                    content: botMessage,
                    timestamp
                }],
                createdAt
            });
            
            const result = await chat_collection.insertOne(newChat);
            return {
                status: 200,
                result,
                chatId
            };
        } else {
            return {
                status: 400,
                message: '找不到該使用者'
            };
        }
    } catch (error) {
        console.error('Error creating new chat:', error);
        // 返回錯誤響應
        return {
            status: 500,
            message: error.message || 'Failed to create new chat'
        };
    }
};
        // if (existingCategory) {
        //     // 類別已存在，返回錯誤響應
        //     return {
        //         status: 400,
        //         message: '類別已存在'
        //     };
        // }

        // const store_custom_category = new CustomStoreCategories({
        //     UniqueID: uuidv4(),
        //     categoryID,
        //     StoreID,
        //     categoryName,
        //     categoryDescription,
        //     createdAt,
        // });

        // const result = await store_custom_categories_collection.insertOne(store_custom_category);

        // // 返回成功響應
        // return {
        //     status: 200,
        //     result
        // };
    