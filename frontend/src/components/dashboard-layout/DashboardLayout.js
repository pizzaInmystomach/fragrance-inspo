'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Header from '@/components/dashboard-layout/Header';
import Breadcrumbs from '@/components/dashboard-layout/Breadcrumbs';
import styles from './DashboardLayout.module.css'
import DynamicBlobsBackground from '../main-layout/DynamicBlobs';

export default function DashboardLayout({ children }) {
    const [isOpen, setIsOpen] = useState(false);
    const router = useRouter();

    const toggleSidebar = () => {
        setIsOpen(!isOpen);
    };

    const breadcrumbItems = [
        { label: 'Fragrance Recommendation', href: '/' },
        { label: 'New Chat' }
    ];

    return (
        <div className={styles.main}>
            <DynamicBlobsBackground>
            <Header/>
            <Breadcrumbs items={breadcrumbItems}/>
            <div>
                {children}
            </div>
            </DynamicBlobsBackground>
        </div>
    );
}