// lib/chat-service.js
// Database service layer for chat functionality using Prisma ORM
import prisma from './prisma';

/**
 * Get chat history for a user
 * @param {string} userId - User ID
 * @returns {Promise<Array>} Chat history
 * 
 * ISSUES IDENTIFIED:
 * 1. No input validation for userId
 * 2. No pagination for potentially large result sets
 * 3. Generic error handling loses specific database error context
 */
export async function getChatHistory(userId) {
    try {
        // Query database for user's chat sessions
        // ISSUE: No validation that userId is valid/exists
        const chatSessions = await prisma.chatSession.findMany({
            where: {
                userId  // Direct userId usage without validation
            },
            orderBy: {
                updatedAt: 'desc'  // Most recent first - good pattern
            },
            include: {
                _count: {
                    select: {
                        messages: true  // Include message count - efficient approach
                    }
                }
            }
        });

        // Transform database results to client-friendly format
        // ISSUE: No handling of null/undefined values in transformation
        return chatSessions.map(session => ({
            id: session.id,
            title: session.title,
            createdAt: session.createdAt,
            updatedAt: session.updatedAt,
            messageCount: session._count.messages
        }));
    } catch (error) {
        // Basic error logging
        console.error('Chat service error:', error);
        // ISSUE: Generic error message masks specific database errors
        throw new Error('Failed to fetch chat history');
    }
}

/**
 * Create a new chat session
 * @param {string} userId - User ID
 * @param {string} title - Chat session title 
 * @returns {Promise<Object>} Created chat session
 * 
 * ISSUES IDENTIFIED:
 * 1. No input validation
 * 2. Default title might not be user-friendly
 * 3. No duplicate session handling
 */
export async function createChatSession(userId, title = 'New Chat') {
    try {
        // Create new chat session in database
        // ISSUE: No validation of userId or title parameters
        // ISSUE: No check if user exists before creating session
        return await prisma.chatSession.create({
            data: {
                userId,    // Direct assignment without validation
                title      // Could be empty string or invalid
            }
        });
    } catch (error) {
        console.error('Chat service error:', error);
        // ISSUE: Same generic error pattern
        throw new Error('Failed to create chat session');
    }
}

/**
 * Get chat messages for a session
 * @param {string} sessionId - Chat session ID
 * @returns {Promise<Array>} Chat messages
 * 
 * ISSUES IDENTIFIED:
 * 1. No pagination for large message histories
 * 2. Complex nested includes without performance considerations
 * 3. No access control (anyone can access any session)
 */
export async function getChatMessages(sessionId) {
    try {
        // Query messages with extensive nested data
        // ISSUE: No validation that sessionId exists or user has access
        const messages = await prisma.chatMessage.findMany({
            where: {
                sessionId  // Direct sessionId usage
            },
            orderBy: {
                createdAt: 'asc'  // Chronological order - appropriate
            },
            include: {
                // ISSUE: Deep nested includes can cause performance problems
                fragranceRecommendations: {
                    include: {
                        fragrance: {
                            include: {
                                notes: true,     // All fragrance notes
                                categories: true // All fragrance categories
                            }
                        }
                    }
                }
            }
        });

        // Transform complex nested data structure
        // ISSUE: Complex mapping logic embedded in service layer
        return messages.map(message => ({
            id: message.id,
            content: message.content,
            sender: message.sender,
            createdAt: message.createdAt,
            // Nested transformation of recommendations
            fragranceRecommendations: message.fragranceRecommendations.map(rec => ({
                id: rec.fragrance.id,
                name: rec.fragrance.name,
                brand: rec.fragrance.brand,
                imageUrl: rec.fragrance.imageUrl,
                // Further nested transformation
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
 * 
 * ISSUES IDENTIFIED:
 * 1. Complex transaction logic for simple operation
 * 2. No validation of messageData structure
 * 3. Inconsistent error handling within transaction
 */
export async function saveChatMessage({
    sessionId,
    content,
    sender,
    fragranceRecommendations = []  // Default empty array - good pattern
}) {
    try {
        // Start database transaction
        // ISSUE: Transaction might be overkill for this operation
        return await prisma.$transaction(async (tx) => {
            // Create the main message record
            // ISSUE: No validation of required fields
            const message = await tx.chatMessage.create({
                data: {
                    sessionId,  // No validation that session exists
                    content,    // No content validation (could be empty)
                    sender      // No sender validation
                }
            });

            // Add fragrance recommendations if provided
            if (fragranceRecommendations.length > 0) {
                // ISSUE: No validation that fragrance IDs exist
                await Promise.all(
                    fragranceRecommendations.map(fragranceId =>
                        tx.fragranceRecommendation.create({
                            data: {
                                messageId: message.id,
                                fragranceId  // Could be invalid ID
                            }
                        })
                    )
                );
            }

            // Update session timestamp
            // ISSUE: This update could fail silently if sessionId is invalid
            await tx.chatSession.update({
                where: { id: sessionId },
                data: { updatedAt: new Date() }
            });

            return message;  // Returns only message, not recommendations
        });
    } catch (error) {
        console.error('Chat service error:', error);
        throw new Error('Failed to save chat message');
    }
}

/*
MAJOR ISSUES SUMMARY:
1. No input validation throughout the module
2. No pagination for potentially large datasets
3. No access control or authorization checks
4. Complex nested queries without performance optimization
5. Generic error handling loses important context
6. No handling of database constraint violations
7. Transaction usage may be unnecessary complexity
8. Data transformation logic mixed with database operations
9. No logging of successful operations for audit trails
10. Missing foreign key validation before operations
*/