// src/Router.jsx
import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

/* ---- Page components ---- */
// import Home from "./Home";          // 首頁元件（請確認檔案路徑）
import Collection from "./collection"; // Fragrance Library 頁面

/* ---- Optional: 404 fallback ---- */
const NotFound = () => <h1 style={{ padding: "2rem" }}>404 ‑ Page Not Found</h1>;

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* <Route path="/" element={<Home />} /> */}
        <Route path="/library" element={<Collection />} />
        {/* 任何未知路徑導到 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}