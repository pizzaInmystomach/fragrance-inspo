'use client';

import styles from './Header.module.css';
import Link from 'next/link';

export default function Header() {
    return (
        <header className={styles.header}>
            <div className={styles.container}>
            <nav>
                <div className={styles.logo}>
                <div className={styles.logoCircle}></div>
                <div className={styles.logoFilled}></div>
                </div>
                <ul className={styles.navLinks}>
                <li><Link href="/">Home</Link></li>
                <li><Link href="#howitworks">How it works</Link></li>
                <li><Link href="#features">Features</Link></li>
                <li><Link href="#blog">Blog</Link></li>
                <li><Link href="#FAQ">FAQ</Link></li>
                </ul>
            </nav>
            </div>
        </header>
    )
}