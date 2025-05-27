'use client';

import styles from './Footer.module.css';

export default function Footer() {
    return (
        <footer className={styles.footer} id="about">
            <div className={styles.container}>
            <p>&copy; {new Date().getFullYear()} Your Personality. Bottled </p>
            </div>
        </footer>
    )
}