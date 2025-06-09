//userSendMessage.js
import clientPromise from "@/lib/mongodb";
import { ObjectId } from "mongodb";
import { aiChatCompletion } from "@/lib/ai-service";
import { getFragrancesByAttributes } from "@/lib/fragrance-service";

export const userSendMessage = async (data) => {
    const client = await clientPromise;
    const db = client.db('fragrance_inspo_app_db');
    const chat_collection = db.collection('users_chat');
    const user_collection = db.collection('users');

    const { userID, chatID, message } = data;
    const userObjectId = new ObjectId(userID);

    try {
        // 檢查使用者是否存在
        const user = await user_collection.findOne({ _id: userObjectId });
        if (!user) {
            return {
                status: 400,
                message: '找不到使用者',
            };
        }

        // 檢查聊天紀錄是否存在
        const chat = await chat_collection.findOne({
            user: userObjectId,
            chatId: chatID,
        });

        if (!chat) {
            return {
                status: 404,
                message: '找不到對應的聊天紀錄',
            };
        }

        const timestamp = new Date().toISOString();

        // 建立使用者訊息
        const userMessage = {
            sender: 'user',
            content: message,
            timestamp,
        };

        // 將使用者訊息推送進 chat 紀錄
        await chat_collection.updateOne(
            { chatId: chatID },
            {
                $push: {
                    messages: userMessage,
                },
            }
        );

        // --- 整合 AI 推薦功能 ---
        let character = null;
        let recommendations = [];
        let botReply = '';

        try {
            // 獲取聊天歷史記錄用於 AI 分析
            const updatedChat = await chat_collection.findOne({
                user: userObjectId,
                chatId: chatID,
            });

            // 建立聊天歷史格式供 AI 分析
            const chatHistory = updatedChat.messages
                .filter(msg => msg.sender === 'user') // 只取用戶訊息用於分析
                .map(msg => ({
                    role: 'user',
                    content: msg.content
                }));

            // 如果沒有聊天歷史，至少用當前訊息
            if (chatHistory.length === 0) {
                chatHistory.push({ role: 'user', content: message });
            }

            // 調用 AI 服務
            const aiResult = await aiChatCompletion(chatHistory);
            character = aiResult.character;
            recommendations = aiResult.recommendations || [];

            // 如果 AI 沒有回傳推薦清單，使用資料庫 fallback
            if (!recommendations.length && character) {
                recommendations = await getFragrancesByAttributes({
                    personality: character.personality,
                    notes: character.notes,
                });
            }

            // 產生 bot 回覆訊息
            if (character && recommendations.length > 0) {
                botReply = `基於您的訊息，我分析您的個性特質是：${character.personality || '獨特且有趣'}。為您推薦了 ${recommendations.length} 款香水！`;
            } else {
                botReply = `感謝您的訊息！我正在為您分析最適合的香水推薦。`;
            }

            // 建立 bot 回覆訊息並存入資料庫
            const botMessage = {
                sender: 'bot',
                content: botReply,
                timestamp: new Date().toISOString(),
                // 可選：將分析結果也存入訊息中
                metadata: {
                    character: character,
                    recommendationCount: recommendations.length
                }
            };

            await chat_collection.updateOne(
                { chatId: chatID },
                {
                    $push: {
                        messages: botMessage,
                    },
                }
            );

        } catch (aiError) {
            console.error('AI service error:', aiError);
            // AI 失敗時的 fallback 回覆
            botReply = '感謝您的訊息！我會儘快為您提供香水推薦。';
            
            const fallbackBotMessage = {
                sender: 'bot',
                content: botReply,
                timestamp: new Date().toISOString(),
            };

            await chat_collection.updateOne(
                { chatId: chatID },
                {
                    $push: {
                        messages: fallbackBotMessage,
                    },
                }
            );
        }

        return {
            status: 200,
            message: '訊息已儲存並處理完成',
            botReply: botReply,
            character: character,
            recommendations: recommendations,
        };

    } catch (error) {
        console.error('Error sending message:', error);
        return {
            status: 500,
            message: error.message || '無法發送訊息',
        };
    }
};