// lib/ai-service.js
// Service module for handling communication with external AI service
// import { headers } from 'next/headers';
// import fetch from 'node-fetch';

// --Environment
const AI_SERVICE_URL = process.env.AI_SERVICE_URL;
const AI_SERVICE_API_KEY = process.env.AI_SERVICE_API_KEY;
if (!AI_SERVICE_URL) throw new Error('AI_SERVICE_URL not set');
if (!AI_SERVICE_API_KEY) throw new Error('AI_SERVICE_URL not set');

// --Helpers
/* Basic shape guard - message must be npn-empty array of { role, content } */
/* Basic validation – return true **if invalid** */
const isInvalidMessages = (msgs) =>
  !Array.isArray(msgs) ||
  msgs.length === 0 ||
  !msgs.every(
    (m) =>
      m &&
      (m.role === 'user' || m.role === 'ai') &&
      typeof m.content === 'string' &&
      m.content.trim().length > 0,
  );

/** fetch with abort timeout (default 30s) */
async function fetchWithTimeout(url, opts, timeoutMs = 30_000) {
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
        if (isInvalidMessages(messages)) {
            throw new Error(
                'aiChatCompletion expects an array of {role, content} objects',
            );
        }

        // 2) Prepare request
        let json;
        try {
            const headers = { 'Content-Type': 'application/json' };
            if (AI_SERVICE_API_KEY) {
              headers.Authorization = `Bearer ${AI_SERVICE_API_KEY}`;
            }

            const res = await fetchWithTimeout(`${AI_SERVICE_URL}/api/recommendations`, {
                method: 'POST',
                headers,
                body: JSON.stringify({
                    character_name: messages[0]?.content ?? '',
                    source_type: 'unknown'
                }),
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
        const { character, recommendations } = json;
        console.log('character: ', character);
        console.log('recommendations: ', recommendations);

        return { character, recommendations };
    } catch (err) {
        console.error('aiChatCompletion failed error: ', err);
        throw new Error('Failed to complete aiChatCompletion. ');
    }
}