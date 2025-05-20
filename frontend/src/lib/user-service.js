// lib/user-service.js
import prisma from './prisma';

/**
 * Get user favorites
 * @param {string} userId - User ID
 * @returns {Promise<Array>} User's favorite fragrances
 */
export async function getUserFavorites(userId) {
    try {
        const favorites = await prisma.favorite.findMany({
        where: {
            userId
        },
        include: {
            fragrance: {
            include: {
                notes: true,
                categories: true
            }
            }
        }
        });

        return favorites.map(fav => ({
        id: fav.fragrance.id,
        name: fav.fragrance.name,
        brand: fav.fragrance.brand,
        description: fav.fragrance.description,
        imageUrl: fav.fragrance.imageUrl,
        categories: fav.fragrance.categories.map(c => c.name),
        notes: fav.fragrance.notes.map(n => n.name),
        price: fav.fragrance.price,
        rating: fav.fragrance.rating,
        addedAt: fav.createdAt
        }));
    } catch (error) {
        console.error('User service error:', error);
        throw new Error('Failed to fetch user favorites');
    }
}

/**
 * Add fragrance to user favorites
 * @param {string} userId - User ID
 * @param {string} fragranceId - Fragrance ID
 * @returns {Promise<Object>} Created favorite
 */
export async function addToFavorites(userId, fragranceId) {
    try {
        // Check if already in favorites
        const existingFavorite = await prisma.favorite.findFirst({
        where: {
            userId,
            fragranceId
        }
        });

        if (existingFavorite) {
        return existingFavorite;
        }

        // Add to favorites
        return await prisma.favorite.create({
        data: {
            user: {
            connect: { id: userId }
            },
            fragrance: {
            connect: { id: fragranceId }
            }
        }
        });
    } catch (error) {
        console.error('User service error:', error);
        throw new Error('Failed to add to favorites');
    }
}

/**
 * Remove fragrance from user favorites
 * @param {string} userId - User ID
 * @param {string} fragranceId - Fragrance ID
 * @returns {Promise<Object>} Deleted favorite
 */
export async function removeFromFavorites(userId, fragranceId) {
    try {
        return await prisma.favorite.deleteMany({
        where: {
            userId,
            fragranceId
        }
        });
    } catch (error) {
        console.error('User service error:', error);
        throw new Error('Failed to remove from favorites');
    }
}