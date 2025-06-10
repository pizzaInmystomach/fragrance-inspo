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

// Typewriter Message Component
const TypewriterMessage = ({ message, isComplete, onComplete }) => {
    const [displayedText, setDisplayedText] = useState('');
    const [currentIndex, setCurrentIndex] = useState(0);
    
    useEffect(() => {
        if (isComplete) {
            setDisplayedText(message.content || message.text);
            return;
        }
        
        if (currentIndex < (message.content || message.text).length) {
            const timer = setTimeout(() => {
                setDisplayedText(prev => prev + (message.content || message.text)[currentIndex]);
                setCurrentIndex(prev => prev + 1);
            }, 30); // 調整打字速度，數字越小越快
            
            return () => clearTimeout(timer);
        } else if (onComplete) {
            onComplete();
        }
    }, [currentIndex, message, isComplete, onComplete]);
    
    return <span>{displayedText}</span>;
};

export default function Chat() {
    const router = useRouter();
    const pathname = usePathname();
    const chatID = pathname.split('/').slice(-1)[0];
    // const userID = localStorage.getItem('userID');
    const [recommendedFragrances, setRecommendedFragrances] = useState([]);
    const [messages, setMessages] = useState([]);
    const [step, setStep] = useState(STEP.NAME);
    const [typingMessageIndex, setTypingMessageIndex] = useState(-1);
    const [isInputDisabled, setIsInputDisabled] = useState(false);
    const [currentCharacter, setCurrentCharacter] = useState(null);
    const [chatLoading, setChatLoading] = useState(true);
    const [userID, setUserID] = useState(null);

    const getUserID = async() => {
        try {
            const response = await axios.get('/api/auth/verify');
            const data = await response.data;
            if (data.status === 200) {
                const userID = data.user.id;
                setUserID(userID);
                await handleFindChatExists(userID);
            } else {
                console.error('Error fetching user ID:', data.message);
                router.push('/chat/not-found');
            }
        } catch (error) {
            console.error('Error fetching user ID:', error);
            router.push('/chat/not-found');
        }
    }

    const handleFindChatExists = async (userID) => {
        try {
            const response = await axios.get(`/api/get-chat?userID=${userID}&chatID=${chatID}`);
            
            if (response.data.status === 200) {
                const data = response.data;
                const messages = data.chat.messages;
                setMessages(messages);
                setChatLoading(false);
            } else {
                router.push('/chat/not-found');
            }
        } catch (error) {
            console.error('Error fetching messages:', error);
            router.push('/chat/not-found');
        }
    }
    useEffect(() => {
        getUserID();
    }, []);
    
    
  
    const appendBotMessage = (text) => {
        const newMessage = { sender: 'bot', text, isTyping: true };
        setMessages(prev => {
            const newMessages = [...prev, newMessage];
            setTypingMessageIndex(newMessages.length - 1);
            setIsInputDisabled(true);
            return newMessages;
        });
    };
  
    const appendUserMessage = (text) => {
      setMessages(prev => [...prev, { sender: 'user', text }]);
    };

    const handleTypingComplete = () => {
        setTypingMessageIndex(-1);
        setIsInputDisabled(false);
        setMessages(prev => 
            prev.map((msg, index) => 
                index === prev.length - 1 && msg.sender === 'bot' 
                    ? { ...msg, isTyping: false } 
                    : msg
            )
        );
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
  
              // const data = await res.json();
              // // data: { message, fragrance }
              // appendBotMessage(data.message || 'Here are some suggestions. ');
              // setRecommendedFragrances(data.fragrances ?? []);
  
              const { character, recommendations } = await res.json();
  
              if(character?.analysis){
                  appendBotMessage(character.analysis);
              }else {
                  appendBotMessage('Here are some suggestions. ')
              }
  
              setRecommendedFragrances(recommendations ?? []);
          } catch (err) {
              console.error(err);
              appendBotMessage('Sorry, something went wrong. ');
              setRecommendedFragrances(SAMPLE_FRAGRANCES);
          } finally {
              setStep(STEP.DONE);
          }
      };

    // const handleUserSendMessage = async (message) => {
    //     appendUserMessage(message); // 顯示使用者訊息
    //     try {
    //         const response = await axios.post('/api/chat/send-message', {
    //             userID: userID,
    //             chatID: chatID,
    //             message: message,
    //         });
    //         const data = await response.data;

    //         if (data.result.status === 200) {
    //             // const { character, message: botMessage, recommendations } = res.data;

    //             // // 顯示 AI 回覆訊息
    //             if (data.result.botReply) {
    //                 appendBotMessage(data.result.botReply);
    //             }

    //             // // 顯示個性分析文字（如果有）
    //             // if (character?.analysis) {
    //             //     appendBotMessage(character.analysis);
    //             // }

    //             // 推薦香水
    //             // setRecommendedFragrances(recommendations ?? []);
    //             // 立即顯示 bot 回覆
    //             // if (result.botReply) {
    //             // displayMessage(result.botReply, 'bot');
    //             // }
                
    //             // // 如果有推薦資料也一併處理
    //             // if (result.recommendations && result.recommendations.length > 0) {
    //             // displayRecommendations(result.recommendations);
    //             // }
    //             setRecommendedFragrances(SAMPLE_FRAGRANCES ?? []);
    //         } else {
    //             throw new Error(`API error ${res.status}`);
    //         }
    //     } catch (err) {
    //         console.error(err);
    //         // appendBotMessage('Sorry, something went wrong.');
    //         setRecommendedFragrances(SAMPLE_FRAGRANCES);
    //     }
    // };

    const handleUserSendMessage = async (message) => {
        appendUserMessage(message);
        
        try {
            console.log('Sending message to backend:', { userID, chatID, message });
            
            const response = await axios.post('/api/chat/send-message', {
                userID: userID,
                chatID: chatID,
                message: message,
            });
            
            const data = response.data;
            console.log('Backend response:', data);

            if (data.result && data.result.status === 200) {
                // 顯示 AI 回覆訊息
                if (data.result.botReply) {
                    appendBotMessage(data.result.botReply, {
                        character: data.result.character,
                        recommendationCount: data.result.recommendations?.length || 0
                    });
                }

                // 更新角色資訊
                if (data.result.character) {
                    setCurrentCharacter(data.result.character);
                }

                // 更新推薦香水
                if (data.result.recommendations && data.result.recommendations.length > 0) {
                    setRecommendedFragrances(data.result.recommendations);
                } else {
                    // 如果沒有 AI 推薦，使用樣本數據
                    setRecommendedFragrances(SAMPLE_FRAGRANCES);
                }
            } else {
                throw new Error(data.message || 'API request failed');
            }
        } catch (err) {
            console.error('Error sending message:', err);
            
            // 錯誤處理：顯示錯誤訊息並提供 fallback
            appendBotMessage('抱歉，處理您的訊息時發生了錯誤。讓我為您提供一些基本推薦。');
            setRecommendedFragrances(SAMPLE_FRAGRANCES);
        }
    };

  
    return (
        <div className={styles.chatContent}>
            {chatLoading && <div className={styles.loadingChat}>Loading...</div>}
            {!chatLoading && <div className={styles.messageBubbleContainer}>
                {/* {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={`${styles.messageBubble} ${msg.sender === 'bot' ? styles.botBubble : styles.userBubble}`}
                    >
                        {msg.content || msg.text}
                    </div>
                ))} */}
                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={`${styles.messageBubble} ${msg.sender === 'bot' ? styles.botBubble : styles.userBubble}`}
                    >
                        {msg.sender === 'bot' && msg.isTyping ? (
                            <TypewriterMessage 
                                message={msg}
                                isComplete={typingMessageIndex !== idx}
                                onComplete={typingMessageIndex === idx ? handleTypingComplete : undefined}
                            />
                        ) : (
                            msg.content || msg.text
                        )}
                    </div>
                ))}
            </div>}

            {step === STEP.NAME && (
                <MessageInput
                    onSend={handleUserSendMessage}
                />
            )}
    
            {step === STEP.DONE && (
                <>
                    <div className={styles.recommendationSection}>
                        <div className={styles.selectedPersonality}>
                            {/* Reset button can be added here if needed */}
                        </div>
            
                        {recommendedFragrances.length > 0 && (
                            <FragranceRecommendation
                                fragrances={recommendedFragrances}
                                recommendations={recommendedFragrances}
                                title="Here are three fragrances I recommend."
                            />
                        )}
                    </div>
                    <MessageInput
                        onSend={handleUserSendMessage}
                        customInputPlaceholder="Ask me anything about fragrances…"
                    />
                </>
            )}
        </div>
        
    );
}

