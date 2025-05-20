import React, { useState } from 'react';
import styles from './ChatHistorySidebar.module.css';
import { IoIosAddCircle } from "react-icons/io";

function ChatHistorySidebar({ chatHistory, onSelectChat }) {
    const [isExpanded, setIsExpanded] = useState(true);

    const toggleSidebar = () => {
        setIsExpanded(!isExpanded);
    };

    const SAMPLE_CHAT_HISTORY = [
        { id: '1', title: 'Winter Warmth', timestamp: '2天前' },
        { id: '2', title: 'Spring Bloom', timestamp: '5天前' },
    ];

    return (
        <div className={`
            ${styles.sidebar}
        `}>
        <div className={styles.sidebarContent}>
            <button className={styles.newChatButton}>
                <IoIosAddCircle className={styles.newChatIcon} onClick={toggleSidebar} />
                <span>New Chat</span>
            </button>
            <div className={styles.chatHistoryList}>
                <p>History</p>
                {chatHistory.map((chat) => (
                    <button 
                    key={chat.id} 
                    className={styles.chatHistoryItem}
                    onClick={() => onSelectChat?.(chat.id)}
                    >
                    {isExpanded ? (
                        <>
                        <span className={styles.chatTitle}>{chat.title}</span>
                        <span className={styles.chatTimestamp}>{chat.timestamp}</span>
                        </>
                    ) : (
                        <span className={styles.chatTitleCollapsed}>
                        {chat.title.charAt(0)}
                        </span>
                    )}
                    </button>
                ))}
            </div>
        </div>
        </div>
    );
}

export default ChatHistorySidebar;