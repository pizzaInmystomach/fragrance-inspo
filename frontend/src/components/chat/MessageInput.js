// MessageInput.js
// React component for handling user message input in chat interface
'use client';  // Next.js client component directive

import React, { useState } from 'react';
import styles from './MessageInput.module.css';

/**
 * MessageInput Component
 * @param {Function} onSend - Callback function for sending messages (UNUSED)
 * @param {string} className - Additional CSS classes (UNUSED)
 * @param {string} customInputPlaceholder - Placeholder text for input field
 * 
 * CRITICAL ISSUES IDENTIFIED:
 * 1. Accepts onSend prop but never uses it
 * 2. Accepts className prop but never applies it
 * 3. Uses onSelect function that is not defined anywhere
 * 4. Has unused message state variable
 * 5. Component interface doesn't match its actual functionality
 */
export default function MessageInput({ 
    onSend,                    // ISSUE: Accepted but never used
    onSelect, 
    className,                 // ISSUE: Accepted but never used
    customInputPlaceholder = 'You can also enter other preferences or questions...'
}) {
    // ISSUE: message state is declared but never used
    const [message, setMessage] = useState('');
    
    // State for custom input field
    const [customInput, setCustomInput] = useState('');

    /**
     * Handles submission of custom input
     * CRITICAL ISSUE: Uses undefined onSelect function instead of onSend prop
     */
    const handleCustomInputSubmit = () => {
        // Check if input has content (good validation)
        if (customInput.trim()) {
            // ISSUE: onSelect is not defined - this will cause runtime error
            // Should probably use onSend prop instead
            onSelect({
                id: 'custom',
                label: 'Custom Preference',
                description: customInput.trim()
            });
            // Clear input after submission (good UX)
            setCustomInput('');
        }
    };

    // Component render
    return (
        <div className={styles.customInputContainer}>
            {/* Input field for custom message */}
            <input
                type="text"
                className={styles.customInput}
                value={customInput}
                onChange={(e) => setCustomInput(e.target.value)}
                placeholder={customInputPlaceholder}
                // ISSUES: Missing accessibility attributes
                // ISSUES: No onKeyPress handler for Enter key submission
                // ISSUES: No maxLength validation
            />
            
            {/* Submit button */}
            <button 
                className={styles.customInputSubmit}
                onClick={handleCustomInputSubmit}
                // ISSUES: Missing accessibility attributes (aria-label, type)
                // ISSUES: No disabled state handling
                // ISSUES: No loading state indication
            >
                {/* SVG send icon - hardcoded inline */}
                <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    width="24" 
                    height="24" 
                    viewBox="0 0 24 24" 
                    fill="none" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round"
                >
                    <path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z" />
                </svg>
            </button>
        </div>
    );
}

/*
CRITICAL ISSUES SUMMARY:
1. MAJOR: Uses undefined onSelect function - will cause runtime errors
2. MAJOR: onSend prop is completely ignored despite being primary purpose
3. MAJOR: Component name suggests message input but creates preference objects
4. Unused state variables (message) indicate incomplete refactoring
5. Missing keyboard navigation (Enter key support)
6. No accessibility features (ARIA labels, roles)
7. No input validation or length limits
8. No error handling for failed submissions
9. Inconsistent prop usage (accepts but ignores className)
10. Hardcoded object structure in onSelect call
11. No loading or disabled states
12. SVG icon should be extracted to separate component

ARCHITECTURAL PROBLEMS:
- Component interface doesn't match implementation
- Appears to be partially refactored code with remnants of old functionality
- Mixing message input with preference selection concepts
- No clear separation of concerns
*/