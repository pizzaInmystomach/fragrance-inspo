'use client';

import React, { useState } from 'react';
import ChatHistorySidebar from './ChatHistorySidebar';
import ChatSelector from './ChatSelector';
import MessageInput from './MessageInput';
import styles from './ChatPageLayout.module.css';

export default function ChatPageLayout({ children }) {
    const SAMPLE_CHAT_HISTORY = [
        { id: '1', title: 'Winter Warmth', timestamp: '2天前' },
        { id: '2', title: 'Spring Bloom', timestamp: '5天前' },
    ];
    return (
        <div className={styles.chatPageLayout}>
            <ChatHistorySidebar
                chatHistory={SAMPLE_CHAT_HISTORY}
                onChatSelect={(chat) => console.log(chat)}
            />
            <div className={styles.chatContent}>
                {children}
                <MessageInput
                    onSend={(message) => console.log(message)}
                    className={styles.messageInput}
                />
            </div>
        </div>
    );
}