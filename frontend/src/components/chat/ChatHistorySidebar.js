"use client";

import React, { useState, useEffect, } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import styles from './ChatHistorySidebar.module.css';
import { IoIosAddCircle } from "react-icons/io";
import { TbDots } from "react-icons/tb";
import axios from 'axios';
import Link from 'next/link';
import { DropdownMenu, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { ChatItemActionsDropdownMenu } from './ChatItemActionsDropdown';

function ChatHistorySidebar() {
    const router = useRouter();
    const pathname = usePathname();
    const currentSelectedChatID = pathname.split('/').slice(-1)[0];
    
    const [isExpanded, setIsExpanded] = useState(true);
    const [chatHistory, setChatHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [openActionDropdownMenuChatID, setOpenActionDropdownMenuChatID] = useState(null);

    const [currentChat, setCurrentChat] = useState(null);

    useEffect(() => {
        loadChatHistory();
    }, []);

    // const userID = localStorage.getItem('userID');
    const userID = '684713347dc983cd4a0ccddd';
    const loadChatHistory = async () => {
        try {
            const response = await axios.get(`/api/all-chats`+`?userID=${userID}`);
            const data = await response.data;
            
            if (response.status === 200 && Array.isArray(data.result)) {
                // 轉換格式：把 _id 改為 id、createdAt 格式化等
                const chats = data.result.map((chat) => ({
                    id: chat._id,
                    chatId: chat.chatId,
                    title: chat.title,
                    timestamp: new Date(chat.createdAt).toLocaleString()
                }));

                setChatHistory(chats);
            } else {
                console.error('Failed to load chat history:', data.error);
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleNewChat = async () => {
        try {
            const response = await axios.post('/api/new-chat', {
                userID: userID
            });
            const data = await response.data;
            if (data.result.status === 200) {
                // 重新載入聊天歷史
                await loadChatHistory();
                const chatId = data.result.chatId;
                setCurrentChat(chatId);
                await handleGetChatByChatID(chatId);
            }
        } catch (error) {
            console.error('Error creating new chat:', error);
        }
    };

    const handleGetChatByChatID = async (chatId) => {
        try {
            const response = await axios.get(`/api/get-chat?userID=${userID}&chatID=${chatId}`);
            const data = await response.data;
            if (data.status === 200) {
                // 導航到新聊天
                router.push(`/chat/${chatId}`);
            }
        } catch (error) {
            console.error('Error creating new chat:', error);
        }
    };

    const handleChatSelect = (chatId) => {
        router.push(`/chat/${chatId}`);
    };

    const toggleSidebar = () => {
        setIsExpanded(!isExpanded);
    };

    return (
        <div className={styles.sidebar}>
            <div className={styles.sidebarContent}>
                <button 
                    className={styles.newChatButton}
                    onClick={handleNewChat}
                >
                    <IoIosAddCircle className={styles.newChatIcon} />
                    <span>New Chat</span>
                </button>

                <div className={styles.chatHistoryList}>
                    <p>History</p>
                    
                    {chatHistory.map((chat) => {
                        const isDropdownOpen = openActionDropdownMenuChatID === chat.chatId;
                        return (
                            <div 
                                key={chat.chatId}
                                className={`
                                    ${styles.chatHistoryItem}
                                    ${currentSelectedChatID === chat.chatId ? styles.activeChatItem : ''}
                                `}
                                onClick={() => handleChatSelect(chat.chatId)}
                            >
                                <Link
                                    href={`/chat/${chat.chatId}`}
                                    className={styles.chatTitle}
                                >
                                    <span>{chat.title}</span>
                                </Link>
                                <DropdownMenu
                                    onOpenChange={(open) => {
                                        setOpenActionDropdownMenuChatID(open ? chat.chatId : null);
                                    }}
                                >
                                    <DropdownMenuTrigger asChild>
                                    <div
                                        className={`
                                            ${styles.actionButton}
                                            ${isDropdownOpen ? styles.open : ''}
                                        `}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setOpenActionDropdownMenuChatID(isDropdownOpen ? null : chat.chatId);
                                        }}
                                    >
                                        <TbDots className={styles.actionIcon} />
                                    </div>
                                    </DropdownMenuTrigger>
                                    <ChatItemActionsDropdownMenu originalTitle={chat.title} userID={userID} chatID={chat.chatId} />
                                </DropdownMenu>
                            </div>
                        )
                        
                    })}
                </div>
            </div>
        </div>
    );
}

export default ChatHistorySidebar;
