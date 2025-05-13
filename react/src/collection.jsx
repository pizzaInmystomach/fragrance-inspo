

// src/collection.js
// Fragrance Library page – displays a searchable grid of perfume cards
// NOTE: Adjust image paths, perfume data, and styling as needed.

import React, { useState, useMemo } from "react";
import "./collection.css";

/** -------------------------------
 *  Dummy data – replace with API or props later
 *  ------------------------------*/
const perfumes = [
  {
    id: 1,
    name: "Chanel No. 5",
    brand: "Chanel",
    image: "/images/chanel_no5.png",
    notes: ["Floral", "Aldehydic", "Powdery"],
    rating: 4.8,
  },
  {
    id: 2,
    name: "Dior Sauvage",
    brand: "Dior",
    image: "/images/dior_sauvage.png",
    notes: ["Fresh", "Spicy", "Amber"],
    rating: 4.6,
  },
  {
    id: 3,
    name: "Jo Malone Peony & Blush Suede",
    brand: "Jo Malone",
    image: "/images/jo_peony.png",
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
    <section className="collection-page">
      {/* Header */}
      <header className="collection-header">
        <h1 className="title">Fragrance Library</h1>

        {/* Search box */}
        <input
          type="search"
          className="search-input"
          placeholder="Search by name, brand, or note…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </header>

      {/* Grid */}
      <div className="grid">
        {filteredPerfumes.map((p) => (
          <article key={p.id} className="card">
            <img
              src={p.image}
              alt={p.name}
              className="card-img"
              loading="lazy"
            />

            <h2 className="card-name">{p.name}</h2>
            <p className="card-brand">{p.brand}</p>

            <ul className="notes">
              {p.notes.map((n) => (
                <li key={n}>{n}</li>
              ))}
            </ul>

            <span className="rating">{p.rating.toFixed(1)} ★</span>
          </article>
        ))}

        {/* Empty state */}
        {filteredPerfumes.length === 0 && (
          <p className="empty">No matching fragrances.</p>
        )}
      </div>
    </section>
  );
}