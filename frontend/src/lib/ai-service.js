// lib/ai-service.js
// Service module for handling communication with external AI service
import { headers } from 'next/headers';
// import fetch from 'node-fetch';

// --Environment
const AI_SERVICE_URL = process.env.AI_SERVICE_URL;
const AI_SERVICE_API_KEY = process.env.AI_SERVICE_API_KEY;
if (!AI_SERVICE_URL) throw new Error('AI_SERVICE_URL not set'); 
if (!AI_SERVICE_API_KEY) throw new Error('AI_SERVICE_API_KEY not set');

// --Helpers
/* Basic shape guard - message must be npn-empty array of { role, content } */
const isValidMessages = (msgs) =>
    Array.isArray(msgs) && msgs.every(
        (m) =>
            m && (m.role === 'user' || m.role === 'ai') && typeof m.content === 'string' && m.content.trim().length > 0,
    );

/** fetch with abort timeout (default 10s) */
async function fetchWithTimeout(url, opts, timeoutMs = 10_000) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
        return await fetch(url, { ...opts, signal: ctrl.signal });
    } finally {
        clearTimeout(timer);
    }
}

/**
 * aiChatCompletion
 * Sends chat messages to the AI service and returns {message, analysis}
 * @param {Array<{role: 'user' | 'ai', content: string}>} messages 
 */

export async function aiChatCompletion(messages) {
    try {
        // 1) validate input early
        if (isValidMessages(messages)) {
            throw new Error(
                'aiChatCompletion expects an array of {role, content} objects',
            );
        }

        // 2) Prepare request
        let json;
        try {
            const res = await fetchWithTimeout(`${AI_SERVICE_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${AI_SERVICE_API_KEY }`,
                },
                body: JSON.stringify({ messages }),
            });

            // 3) Handle non-2xx HTTP
            if (!res.ok) {
                const text = await res.text().catch(() => '');
                throw new Error(
                    `AI service responded ${res.status} - ${text || res.statusText}`,
                );
            }

            json = await res.json();
        } catch (err) {
            console.error('aiChatCompletion network error:', err);
            throw new Error('Failed to reach AI service');
        }

        // 4) Normalise response
        const {
            messages,
            analysis = {},
            needs_recommendation: needsRecLegacy,
        } = json;

        return {
            message: typeof message === 'string' ? message : '',
            analysis: {
                personality: analysis.personality ?? null,
                notes: analysis.notes ?? [],
                specificRequest: analysis.specificRequest ?? null,
                needsRecommendation:
                    typeof analysis.needs_recommendation === 'boolean'
                    ? analysis.needsRecommendation
                    : Boolean(needsRecLegacy),
            },
        };
    } catch (err) {
        console.error('aiChatCompletion failed error: ', err);
        throw new Error('Failed to complete aiChatCompletion. ');
    }
}