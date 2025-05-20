// Fragrance Inspo - Chat

// Chat with your fragrance AI assistant
// Features:
// - Select personality type
// - Select fragrance notes
// - Receive fragrance recommendations
// - Chat Messages History

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ChatSelector from '@/components/chat/ChatSelector';
import FragranceRecommendation from '@/components/chat/FragranceRecommendation';
import styles from './Chat.module.css';

const STEP = {
    PERSONALITY: 'personality',
    NOTE: 'note',
    DONE: 'done',
};

const SAMPLE_PERSONALITY_OPTIONS = [
{
    id: 'introvert',
    icon: '🧘',
    label: 'Introverted',
    description: 'Likes to be alone, enjoys quiet time'
},
{
    id: 'active',
    icon: '💪',
    label: 'Active',
    description: 'Loves sports, enjoys being outdoors'
},
{
    id: 'dreamy',
    icon: '✨',
    label: 'Dreamy',
    description: 'Creative, enjoys art and imagination'
}
];

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
    const [selectedPersonality, setSelectedPersonality] = useState(null);
    const [selectedNote, setSelectedNote] = useState(null);
    const [recommendedFragrances, setRecommendedFragrances] = useState([]);
    const [messages, setMessages] = useState([]);
    const [step, setStep] = useState(STEP.PERSONALITY);
  
    const appendBotMessage = (text) => {
      setMessages(prev => [...prev, { sender: 'bot', text }]);
    };
  
    const appendUserMessage = (text) => {
      setMessages(prev => [...prev, { sender: 'user', text }]);
    };
  
    // First Render - bot message
    useEffect(() => {
      appendBotMessage('Select the description that best matches your personality:');
    }, []);
  
    const handlePersonalitySelect = (personality) => {
        setSelectedPersonality(personality);
        appendUserMessage(personality.label);
        setTimeout(() => {
            appendBotMessage('Now, please select the fragrance note you prefer:');
            setStep(STEP.NOTE);
        }, 500);
    };
  
    const handleNoteSelect = (note) => {
        setSelectedNote(note);
        appendUserMessage(note.label);
        setStep(STEP.DONE);
        // mock
        setRecommendedFragrances(SAMPLE_FRAGRANCES);
    };
  
    const NOTE_OPTIONS = [
        { id: 'citrus', icon: '🍊', label: 'Citrus' },
        { id: 'woody', icon: '🌲', label: 'Woody' },
        { id: 'floral', icon: '🌸', label: 'Floral' },
    ];
  
    return (
        <div className={styles.chatContent}>
            <div className={styles.messageBubbleContainer}>
                {messages.map((msg, idx) => (
                    <div
                    key={idx}
                    className={`${styles.messageBubble} ${msg.sender === 'bot' ? styles.botBubble : styles.userBubble}`}
                    >
                    {msg.text}
                    </div>
                ))}
            </div>
    
            {step === STEP.PERSONALITY && (
            <ChatSelector
                options={SAMPLE_PERSONALITY_OPTIONS}
                onSelect={handlePersonalitySelect}
            />
            )}
    
            {step === STEP.NOTE && (
            <ChatSelector
                options={NOTE_OPTIONS}
                onSelect={handleNoteSelect}
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
