// app/api/collection/route.js

import { NextResponse } from 'next/server';
import { getUserFavorites, addToFavorites, removeFromFavorites } from '@/lib/user-service';

// Get user collection
export async function GET(request) {
    try {
        const { searchParams } = new URL(request.url);
        const userId = searchParams.get('userId');
        
        if (!userId) {
        return NextResponse.json(
            { error: 'User ID is required' },
            { status: 400 }
        );
        }
        
        const favorites = await getUserFavorites(userId);
        return NextResponse.json({ favorites });
    } catch (error) {
        console.error('Favorites API error:', error);
        return NextResponse.json(
        { error: 'Failed to fetch collection' },
        { status: 500 }
        );
    }
}

// Add to collection
export async function POST(request) {
    try {
        const data = await request.json();
        const { userId, fragranceId } = data;
        
        if (!userId || !fragranceId) {
        return NextResponse.json(
            { error: 'User ID and fragrance ID are required' },
            { status: 400 }
        );
        }
        
        await addToFavorites(userId, fragranceId);
        return NextResponse.json({ success: true });
    } catch (error) {
        console.error('Add to favorites API error:', error);
        return NextResponse.json(
        { error: 'Failed to add to collection' },
        { status: 500 }
        );
    }
}

// Remove from collection
export async function DELETE(request) {
    try {
        const data = await request.json();
        const { userId, fragranceId } = data;
        
        if (!userId || !fragranceId) {
        return NextResponse.json(
            { error: 'User ID and fragrance ID are required' },
            { status: 400 }
        );
        }
        
        await removeFromFavorites(userId, fragranceId);
        return NextResponse.json({ success: true });
    } catch (error) {
        console.error('Remove from favorites API error:', error);
        return NextResponse.json(
        { error: 'Failed to remove from collection' },
        { status: 500 }
        );
    }
}