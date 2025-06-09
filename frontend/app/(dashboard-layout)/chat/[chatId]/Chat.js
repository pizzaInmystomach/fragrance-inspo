'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import ChatSelector from '@/components/chat/ChatSelector';
import FragranceRecommendation from '@/components/chat/FragranceRecommendation';
import styles from './Chat.module.css';
import MessageInput from '@/components/chat/MessageInput';
import axios from 'axios';

const STEP = {
    NAME: 'name', 
    DONE: 'done',
};

const SAMPLE_FRAGRANCES = [
{
    id: '1',
    name: 'Oud Royal',
    brand: 'Giorgio Armani Privé',
    imageUrl: '/fragrance01.png',
    categories: ['Woody', 'Oriental']
},
{
    id: '2',
    name: 'Blood Oranges',
    brand: 'Shay & Blue',
    imageUrl: '/fragrance02.png',
    categories: ['Fruity', 'Citrus']
},
{
    id: '3',
    name: 'Sartorial',
    brand: 'Penhaligon\'s',
    imageUrl: '/fragrance03.png',
    categories: ['Woody', 'Spicy']
}
];

export default function Chat() {
    const [recommendedFragrances, setRecommendedFragrances] = useState([]);
    const [messages, setMessages] = useState([]);
    const [step, setStep] = useState(STEP.NAME);
    const router = useRouter();
    const pathname = usePathname();
    const chatID = pathname.split('/').slice(-1)[0];
    const userID = '684713347dc983cd4a0ccddd'

    const handleGetMessages = async () => {
        try {
            const response = await axios.get(`/api/get-chat`+ `?userID=${userID}&chatID=${chatID}`);
            const data = await response.data;
            const messages = data.chat.messages;
            setMessages(messages);
            } catch (error) {
            console.error('Error fetching messages:', error);
        }
    }
    const handleFindChatExists = async () => {
        try {
            const response = await axios.get(`/api/get-chat?userID=${userID}&chatID=${chatID}`);
            
            if (response.status === 200) {
                const data = response.data;
                if (data.chat && data.chat.messages) {
                    setMessages(data.chat.messages);
                } else {
                    router.push('/chat/not-found');
                }
            } else {
                router.push('/chat/not-found');
            }
        } catch (error) {
            console.error('Error fetching messages:', error);
            router.push('/chat/not-found');
        }
    }
    
    useEffect(() => {
        handleFindChatExists();
    }, []);
    
    
  
    const appendBotMessage = (text) => {
      setMessages(prev => [...prev, { sender: 'bot', text }]);
    };
  
    const appendUserMessage = (text) => {
      setMessages(prev => [...prev, { sender: 'user', text }]);
    };
    
    const handleNameSubmit = async (name) => {
        appendUserMessage(name);
        try{
            console.log('POSTing to /chat...')
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name }),
            });

            if(!res.ok) throw new Error(`API error ${res.status}`);

            const data = await res.json();
            // data: { message, fragrance }
            appendBotMessage(data.message || 'Here are some suggestions. ');
            setRecommendedFragrances(data.fragrances ?? []);
        } catch (err) {
            console.error(err);
            appendBotMessage('Sorry, something went wrong. ');
            setRecommendedFragrances(SAMPLE_FRAGRANCES);
        } finally {
            setStep(STEP.DONE);
        }
    };
  
    return (
        <div className={styles.chatContent}>
            <div className={styles.messageBubbleContainer}>
                {messages.map((msg, idx) => (
                    <div
                    key={idx}
                    className={`${styles.messageBubble} ${msg.sender === 'bot' ? styles.botBubble : styles.userBubble}`}
                    >
                    {msg.content}
                    </div>
                ))}
            </div>

            {step === STEP.NAME && (
                <MessageInput
                    onSend={handleNameSubmit}
                />
            )}
    
            {step === STEP.DONE && (
            <div className={styles.recommendationSection}>
                <div className={styles.selectedPersonality}>
                {/* <button
                    className={styles.resetButton}
                    onClick={() => {
                    setSelectedPersonality(null);
                    setSelectedNote(null);
                    setRecommendedFragrances([]);
                    setMessages([]);
                    setStep(STEP.PERSONALITY);
                    appendBotMessage('Select the description that best matches your personality:');
                    }}
                >
                    Reset
                </button> */}
                </div>
    
                {recommendedFragrances.length > 0 && (
                <FragranceRecommendation
                    fragrances={recommendedFragrances}
                    title="Here are three fragrances I recommend."
                />
                )}
            </div>
            )}
        </div>
    );
  }
