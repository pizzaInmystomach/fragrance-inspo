// lib/ai-service.js
import fetch from 'node-fetch';

const AI_SERVICE_URL = process.env.AI_SERVICE_URL;

/**
 * Sends chat messages to the Python AI service and gets recommendations
 * @param {Array} messages - Chat message history
 * @returns {Promise<Object>} AI response with message and analysis
 */
export async function aiChatCompletion(messages) {
    try {
        const response = await fetch(`${AI_SERVICE_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${process.env.AI_SERVICE_API_KEY}`
        },
        body: JSON.stringify({ messages })
        });

        if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`AI service error: ${errorData.error || response.statusText}`);
        }

        const data = await response.json();
        return {
        message: data.message,
        analysis: data.analysis || {
            personality: null,
            notes: [],
            mood: null,
            occasion: null,
            specificRequest: null,
            needsRecommendation: data.needs_recommendation || false
        }
        };
    } catch (error) {
        console.error('AI service error:', error);
        throw new Error('Failed to get AI response');
    }
}