'use client';

import React, { useEffect } from 'react';
import styles from './Blobs.module.css'; // 確保你有這個 CSS 檔案


export default function BouncingBlobs() {
  useEffect(() => {
    const script = document.createElement('script');
    script.src = '/javascripts/anm_background.js'; // 放在 public 資料夾
    script.async = true;
    document.body.appendChild(script);
    return () => {
      document.body.removeChild(script);
    };
  }, []);

  return (
    <div className={styles.container}>
      <div className={styles.glass}></div>
      <div className={styles.blobs}>
        <div className={`${styles.blob} ${styles.black}`}></div>
        <div className={`${styles.blob} ${styles.blue}`}></div>
        <div className={`${styles.blob} ${styles.black}`}></div>
        <div className={`${styles.blob} ${styles.purple}`}></div>
        <div className={`${styles.blob} ${styles.black}`}></div>
        <div className={`${styles.blob} ${styles.purple}`}></div>
        <div className={`${styles.blob} ${styles.pink}`}></div>
      </div>
    </div>
  );
}
