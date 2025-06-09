'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import ChatSelector from '@/components/chat/ChatSelector';
import FragranceRecommendation from '@/components/chat/FragranceRecommendation';
import styles from './Chat.module.css';
import MessageInput from '@/components/chat/MessageInput';
import axios from 'axios';

export default function Chat() {
    const router = useRouter();
    // const userID = localStorage.getItem('userID');
    const userID = process.env.NEXT_PUBLIC_USER_ID;
    const handleStartNewChat = async () => {
        try {
            const response = await axios.post('/api/new-chat', {
                userID: userID
            })
            const data = await response.data;
            if (data.result.status === 200) {
                window.location.href = `/chat/${data.result.chatId}`;
            }
        } catch (error) {
            console.error('Error creating new chat:', error);
            window.location.href = `/chat`
        }
    }
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
  
    return (
        <div className={styles.chatContent}>
            <div className={styles.chatNotFound}>
                <h1>Chat Not Found</h1>
                <p>Sorry, the chat you requested could not be found.</p>
            </div>
            <div className={styles.startNewChat} onClick={() => handleStartNewChat()}>
                Start A New Chat
            </div>
        </div>
    );
  }
