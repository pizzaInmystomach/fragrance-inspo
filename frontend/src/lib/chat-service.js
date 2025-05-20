// lib/chat-service.js
import prisma from './prisma';

/**
 * Get chat history for a user
 * @param {string} userId - User ID
 * @returns {Promise<Array>} Chat history
 */
export async function getChatHistory(userId) {
    try {
        const chatSessions = await prisma.chatSession.findMany({
        where: {
            userId
        },
        orderBy: {
            updatedAt: 'desc'
        },
        include: {
            _count: {
            select: {
                messages: true
            }
            }
        }
        });

        return chatSessions.map(session => ({
        id: session.id,
        title: session.title,
        createdAt: session.createdAt,
        updatedAt: session.updatedAt,
        messageCount: session._count.messages
        }));
    } catch (error) {
        console.error('Chat service error:', error);
        throw new Error('Failed to fetch chat history');
    }
}

/**
 * Create a new chat session
 * @param {string} userId - User ID
 * @param {string} title - Chat session title 
 * @returns {Promise<Object>} Created chat session
 */
export async function createChatSession(userId, title = 'New Chat') {
    try {
        return await prisma.chatSession.create({
        data: {
            userId,
            title
        }
        });
    } catch (error) {
        console.error('Chat service error:', error);
        throw new Error('Failed to create chat session');
    }
}

/**
 * Get chat messages for a session
 * @param {string} sessionId - Chat session ID
 * @returns {Promise<Array>} Chat messages
 */
export async function getChatMessages(sessionId) {
    try {
        const messages = await prisma.chatMessage.findMany({
        where: {
            sessionId
        },
        orderBy: {
            createdAt: 'asc'
        },
        include: {
            fragranceRecommendations: {
            include: {
                fragrance: {
                include: {
                    notes: true,
                    categories: true
                }
                }
            }
            }
        }
        });

        return messages.map(message => ({
        id: message.id,
        content: message.content,
        sender: message.sender,
        createdAt: message.createdAt,
        fragranceRecommendations: message.fragranceRecommendations.map(rec => ({
            id: rec.fragrance.id,
            name: rec.fragrance.name,
            brand: rec.fragrance.brand,
            imageUrl: rec.fragrance.imageUrl,
            categories: rec.fragrance.categories.map(c => c.name)
        }))
        }));
    } catch (error) {
        console.error('Chat service error:', error);
        throw new Error('Failed to fetch chat messages');
    }
}

/**
 * Save a chat message
 * @param {Object} messageData - Message data
 * @returns {Promise<Object>} Saved message
 */
export async function saveChatMessage({
  sessionId,
  content,
  sender,
  fragranceRecommendations = []
}) {
    try {
        // Start a transaction
        return await prisma.$transaction(async (tx) => {
        // Create the message
        const message = await tx.chatMessage.create({
            data: {
            sessionId,
            content,
            sender
            }
        });

        // Add fragrance recommendations if any
        if (fragranceRecommendations.length > 0) {
            await Promise.all(
            fragranceRecommendations.map(fragranceId =>
                tx.fragranceRecommendation.create({
                data: {
                    messageId: message.id,
                    fragranceId
                }
                })
            )
            );
        }

        // Update the session's updatedAt
        await tx.chatSession.update({
            where: { id: sessionId },
            data: { updatedAt: new Date() }
        });

        return message;
        });
    } catch (error) {
        console.error('Chat service error:', error);
        throw new Error('Failed to save chat message');
    }
}