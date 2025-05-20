

// src/library.js
// Fragrance Library page – displays a searchable grid of perfume cards
// NOTE: Adjust image paths, perfume data, and styling as needed.

'use client';
import React, { useState, useMemo } from "react";
import styles from './Library.module.css'

/** -------------------------------
 *  Dummy data – replace with API or props later
 *  ------------------------------*/
const perfumes = [
  {
    id: 1,
    name: "Chanel No. 5",
    brand: "Chanel",
    image: "/fragrance01.png",
    notes: ["Floral", "Aldehydic", "Powdery"],
    rating: 4.8,
  },
  {
    id: 2,
    name: "Dior Sauvage",
    brand: "Dior",
    image: "/fragrance02.png",
    notes: ["Fresh", "Spicy", "Amber"],
    rating: 4.6,
  },
  {
    id: 3,
    name: "Jo Malone Peony & Blush Suede",
    brand: "Jo Malone",
    image: "/fragrance03.png",
    notes: ["Peony", "Red Apple", "Suede"],
    rating: 4.4,
  },
  // …more items
];

export default function Collection() {
  /* ---------------- State ---------------- */
  const [query, setQuery] = useState("");

  /* ------------- Derived data ------------ */
  const filteredPerfumes = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q
      ? perfumes.filter(
          (p) =>
            p.name.toLowerCase().includes(q) ||
            p.brand.toLowerCase().includes(q) ||
            p.notes.some((n) => n.toLowerCase().includes(q))
        )
      : perfumes;
  }, [query]);

  /* -------------- Rendering -------------- */
  return (
    <section className={styles.collectionPage}>
      {/* Header */}
      <header className={styles.collectionHeader}>
        <h1 className={styles.title}>Fragrance Library</h1>

        {/* Search box */}
        <input
          type="search"
          className={styles.searchInput}
          placeholder="Search by name, brand, or note…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </header>

      {/* Grid */}
      <div className={styles.grid}>
        {filteredPerfumes.map((p) => (
          <article key={p.id} className={styles.card}>
            <img
              src={p.image}
              alt={p.name}
              className={styles.cardImg}
              loading="lazy"
            />

            <h2 className={styles.cardName}>{p.name}</h2>
            <p className={styles.cardBrand}>{p.brand}</p>

            <ul className={styles.notes}>
              {p.notes.map((n) => (
                <li key={n}>{n}</li>
              ))}
            </ul>

            <span className={styles.rating}>{p.rating.toFixed(1)} ★</span>
          </article>
        ))}

        {/* Empty state */}
        {filteredPerfumes.length === 0 && (
          <p className={styles.empty}>No matching fragrances.</p>
        )}
      </div>
    </section>
  );
}