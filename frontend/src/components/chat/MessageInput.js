// MessageInput.js
'use client';

import React, { useState } from 'react';
import PropTypes from 'prop-types';
import styles from './MessageInput.module.css';

/**
 * MessageInput
 *
 * Props
 * -----
 * onSend(text)              – required; called when user submits
 * className                 – optional; additional CSS classes
 * customInputPlaceholder    – optional; placeholder text for <input>
 */
export default function MessageInput({
  onSend,
  className = '',
  customInputPlaceholder = 'Enter the person’s name…',
}) {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    const value = text.trim();
    if (!value) return;
    setLoading(true);
    await onSend?.(value);
    setText('');
    setLoading(false);
  };

  /* ---------- render ---------- */
  return (
    <form
      className={`${styles.customInputContainer} ${className}`}
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
    >
      <input
        type="text"
        className={styles.customInput}
        placeholder={customInputPlaceholder}
        value={text}
        onChange={(e) => setText(e.target.value)}
        maxLength={120}
        disabled={loading}
        aria-label="Chat input"
      />

      <button
        type="submit"
        className={styles.customInputSubmit}
        disabled={loading || !text.trim()}
        aria-label="Send"
      >
        {/* Send icon */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
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
    </form>
  );
}

MessageInput.propTypes = {
  onSend: PropTypes.func.isRequired,
  className: PropTypes.string,
  customInputPlaceholder: PropTypes.string,
};