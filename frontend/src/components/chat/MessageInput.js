'use client';

import React, { useState } from 'react';
import styles from './MessageInput.module.css';

export default function MessageInput({ onSend, className, customInputPlaceholder = 'You can also enter other preferences or questions...'  }) {
    const [message, setMessage] = useState('');
    const [customInput, setCustomInput] = useState('');

    const handleCustomInputSubmit = () => {
        if (customInput.trim()) {
          onSelect({
            id: 'custom',
            label: 'Custom Preference',
            description: customInput.trim()
          });
          setCustomInput('');
        }
      };

    return (
        <div className={styles.customInputContainer}>
            <input
            type="text"
            className={styles.customInput}
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            placeholder={customInputPlaceholder}
            />
            <button 
            className={styles.customInputSubmit}
            onClick={handleCustomInputSubmit}
            >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z" />
            </svg>
            </button>
        </div>
    );
}