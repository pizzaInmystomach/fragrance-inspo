// lib/fragrance-service.js
import prisma from './prisma';

/**
 * Get fragrances by attributes
 * @param {Object} attributes - Fragrance attributes
 * @returns {Promise<Array>} Matching fragrances
 */
export async function getFragrancesByAttributes({
    personality,
    notes = [],
    mood,
    occasion,
    limit = 3
}) {
    try {
        // Build query filters based on provided attributes
        const filters = {};
        
        // Add note filters if provided
        if (notes && notes.length > 0) {
        filters.notes = {
            some: {
            name: {
                in: notes
            }
            }
        };
        }

        // Add personality match if provided
        if (personality) {
        filters.personalityMatch = {
            contains: personality,
            mode: 'insensitive'
        };
        }

        // Add mood match if provided
        if (mood) {
        filters.mood = {
            contains: mood,
            mode: 'insensitive'
        };
        }

        // Add occasion match if provided
        if (occasion) {
        filters.occasion = {
            contains: occasion,
            mode: 'insensitive'
        };
        }

        // Query the database
        const fragrances = await prisma.fragrance.findMany({
        where: filters,
        include: {
            notes: true,
            categories: true
        },
        take: limit
        });

        // Format the results
        return fragrances.map(fragrance => ({
        id: fragrance.id,
        name: fragrance.name,
        brand: fragrance.brand,
        description: fragrance.description,
        imageUrl: fragrance.imageUrl,
        categories: fragrance.categories.map(c => c.name),
        notes: fragrance.notes.map(n => n.name),
        price: fragrance.price,
        rating: fragrance.rating
        }));
    } catch (error) {
        console.error('Fragrance service error:', error);
        throw new Error('Failed to fetch fragrances');
    }
}

/**
 * Get fragrance by ID
 * @param {string} id - Fragrance ID
 * @returns {Promise<Object>} Fragrance details
 */
export async function getFragranceById(id) {
    try {
        const fragrance = await prisma.fragrance.findUnique({
        where: { id },
        include: {
            notes: true,
            categories: true
        }
        });

        if (!fragrance) {
        throw new Error('Fragrance not found');
        }

        return {
        id: fragrance.id,
        name: fragrance.name,
        brand: fragrance.brand,
        description: fragrance.description,
        imageUrl: fragrance.imageUrl,
        categories: fragrance.categories.map(c => c.name),
        notes: fragrance.notes.map(n => n.name),
        price: fragrance.price,
        rating: fragrance.rating
        };
    } catch (error) {
        console.error('Fragrance service error:', error);
        throw new Error('Failed to fetch fragrance');
    }
    }