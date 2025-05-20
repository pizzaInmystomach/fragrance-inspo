'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Header from '@/components/dashboard-layout/Header';
import Breadcrumbs from '@/components/dashboard-layout/Breadcrumbs';

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
        <div>
            <Header/>
            <Breadcrumbs items={breadcrumbItems}/>
            <div>
                {children}
            </div>
        </div>
    );
}