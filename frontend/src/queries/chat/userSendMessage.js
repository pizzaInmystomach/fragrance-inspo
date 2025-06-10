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

            // 建立完整聊天歷史格式供 AI 分析
            const chatHistory = updatedChat.messages.map(msg => ({
                role: msg.sender === 'user' ? 'user' : 'ai',
                content: msg.content
            }));

            // 確保至少有當前訊息
            if (chatHistory.length === 0) {
                chatHistory.push({ role: 'user', content: message });
            }

            console.log('Sending to AI service with chat history:', chatHistory);

            // 調用 AI 服務
            const aiResult = await aiChatCompletion(chatHistory);
            character = aiResult.character;
            recommendations = aiResult.recommendations || [];

            console.log('AI service returned:', { character, recommendations });

            // 如果 AI 沒有回傳推薦清單使用 fallback
            if (!recommendations.length && character) {
                console.log('Using database fallback for recommendations');
                try {
                    recommendations = await getFragrancesByAttributes({
                        personality: character.personality,
                        notes: character.notes,
                        limit: 3
                    });
                } catch (dbError) {
                    console.error('Database fallback error:', dbError);
                    // 如果資料庫失敗使用預設推薦
                    recommendations = [];
                }
            }

            // 產生 bot 回覆訊息
            if (character && recommendations.length > 0) {
                const personalityText = character.personality || '獨特且有趣';
                const analysisText = character.analysis || `我分析您的個性特質是：${personalityText}`;
                botReply = `${analysisText} 為您推薦了 ${recommendations.length} 款香水！`;
            } else if (character && character.analysis) {
                botReply = character.analysis;
            } else {
                botReply = `感謝您的訊息！我正在為您分析最適合的香水推薦。`;
            }

        } catch (aiError) {
            console.error('AI service error:', aiError);
            // AI 失敗時的 fallback 回覆
            botReply = '感謝您的訊息！讓我為您提供一些香水推薦。';
            
            // 嘗試使用基本的資料庫查詢作為 fallback
            try {
                recommendations = await getFragrancesByAttributes({
                    limit: 3
                });
            } catch (dbError) {
                console.error('Database fallback also failed:', dbError);
                recommendations = [];
            }
        }

        // 建立 bot 回覆訊息並存入資料庫
        const botMessage = {
            sender: 'bot',
            content: botReply,
            timestamp: new Date().toISOString(),
            metadata: {
                character: character,
                recommendationCount: recommendations.length,
                hasRecommendations: recommendations.length > 0
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