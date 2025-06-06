// lib/ai-service.js
// Service module for handling communication with external AI service
import fetch from 'node-fetch';

// Environment variable for AI service endpoint - potential issue: no validation
const AI_SERVICE_URL = process.env.AI_SERVICE_URL;
if (!AI_SERVICE_URL) throw new Error('AI_SERVICE_URL not set'); 

/**
 * Sends chat messages to the Python AI service and gets recommendations
 * @param {Array} messages - Chat message history
 * @returns {Promise<Object>} AI response with message and analysis
 * 
 * ISSUES IDENTIFIED:
 * 1. No input validation on messages parameter
 * 2. No timeout handling for fetch request
 * 3. Hardcoded error structure assumptions
 * 4. Missing environment variable validation
 * 5. Inconsistent error handling patterns
 */
export async function aiChatCompletion(messages) {
    try {
        // Making POST request to AI service endpoint
        // ISSUE: No check if AI_SERVICE_URL is defined or valid
        const response = await fetch(`${AI_SERVICE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // ISSUE: No validation if API key exists
                'Authorization': `Bearer ${process.env.AI_SERVICE_API_KEY}`
            },
            // ISSUE: No validation of messages array structure or content
            body: JSON.stringify({ messages })
        });

        // Check if HTTP response is successful
        if (!response.ok) {
            // Attempt to parse error response
            // ISSUE: This could fail if response is not JSON
            const errorData = await response.json();
            // ISSUE: Generic error message construction
            throw new Error(`AI service error: ${errorData.error || response.statusText}`);
        }

        // Parse successful response
        const data = await response.json();
        
        // Return structured response with fallback values
        // ISSUE: Hardcoded default structure - fragile if API contract changes
        return {
            message: data.message,
            analysis: data.analysis || {
                personality: null,           // Default personality analysis
                notes: [],                  // Default notes array
                mood: null,                 // Default mood detection
                occasion: null,             // Default occasion inference
                specificRequest: null,      // Default specific request parsing
                // ISSUE: Inconsistent naming (needs_recommendation vs needsRecommendation)
                needsRecommendation: data.needs_recommendation || false
            }
        };
    } catch (error) {
        // Basic error logging
        console.error('AI service error:', error);
        // ISSUE: Generic error message loses context of original error
        throw new Error('Failed to get AI response');
    }
}

/*
MAJOR ISSUES SUMMARY:
1. No input validation or sanitization
2. Missing environment variable checks
3. No request timeout or retry logic
4. Inconsistent error handling
5. Assumes API response structure without validation
6. No rate limiting considerations
7. Hardcoded fallback values may mask actual API issues
*/