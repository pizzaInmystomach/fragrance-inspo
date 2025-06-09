import React from 'react';
import styles from './FragranceRecommendation.module.css';

/**
 * @param {Object[]} recommendations – array from backend
 *   {
 *     rank: 1,
 *     fragrance: { id, name, brand, imageUrl },
 *     rationale: string,
 *     description: string
 *   }
 */

function FragranceRecommendation({
  recommendations,
  title = 'Fragrance Recommendations',
}) {
  return (
    <div className={styles.recommendationContainer}>
      <h3 className={styles.recommendationTitle}>{title}</h3>
      <div className={styles.fragranceGrid}>
        {recommendations.map((rec) => (
          <div key={rec.fragrance.id} className={styles.fragranceCard}>
            <div className={styles.fragranceImageContainer}>
              <img
                src={rec.fragrance.imageUrl || '/placeholder.png'}
                alt={`${rec.fragrance.name} by ${rec.fragrance.brand}`}
                className={styles.fragranceImage}
              />
              <button className={styles.favoriteButton}>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                </svg>
              </button>
            </div>
            <div className={styles.fragranceDetails}>
              <h4 className={styles.fragranceName}>
                {rec.rank}. {rec.fragrance.name}
              </h4>
              <p className={styles.fragranceBrand}>{rec.fragrance.brand}</p>

              <p className={styles.fragranceRationale}>{rec.rationale}</p>
              <p className={styles.fragranceDescription}>{rec.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default FragranceRecommendation;