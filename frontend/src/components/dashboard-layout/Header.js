'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import styles from './Header.module.css';
import { FaBookmark, FaMessage } from "react-icons/fa6";

function Header({ title = 'FragranceInspo' }) {
  const router = useRouter();
  return (
    <header className={styles.header}>
      <div className={styles.logo}>
        <Link href="/">
          <span className={styles.logoText}>{title}</span>
        </Link>
      </div>
      <div className={styles.actions}>
        <FaMessage className={styles.icon} fontSize={"1.2em"} onClick={() => router.push('/chat')}/>
        <FaBookmark className={styles.icon} fontSize={"1.2em"} onClick={() => router.push('/library')}/>
        <button className={styles.searchButton}>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
        </button>
        <button className={styles.profileButton}>L</button>
      </div>
    </header>
  );
}

export default Header;