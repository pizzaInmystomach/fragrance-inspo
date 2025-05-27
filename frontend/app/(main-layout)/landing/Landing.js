'use client';
import { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import './landing.css';

export default function Landing() {
  const [currentSlide, setCurrentSlide] = useState(0);

  // Testimonial data
  const testimonials = [
    {
      text: "Incredibly accurate! The fragrance the system recommended feels genuinely 'me'.",
      author: "Emily K.",
      age: "32"
    },
    {
      text: "The personality matching system is brilliant. I've found my signature scent!",
      author: "James T.",
      age: "28"
    },
    {
      text: "I was skeptical at first, but the recommended fragrance perfectly captures my essence.",
      author: "Sophia R.",
      age: "35"
    }
  ];

  // Testimonial navigation functions
  const prevSlide = () => {
    setCurrentSlide((prev) =>
      prev === 0 ? testimonials.length - 1 : prev - 1
    );
  };

  const nextSlide = () => {
    setCurrentSlide((prev) =>
      prev === testimonials.length - 1 ? 0 : prev + 1
    );
  };

  return (
    <div>
      <header>
        <div className="container">
          <nav>
            <div className="logo">
              <div className="logo-circle"></div>
              <div className="logo-filled"></div>
            </div>
            <ul className="nav-links">
              <li><Link href="/">Home</Link></li>
              <li><Link href="#howitworks">How it works</Link></li>
              <li><Link href="#features">Features</Link></li>
              <li><Link href="#blog">Blog</Link></li>
              <li><Link href="#FAQ">FAQ</Link></li>
            </ul>
          </nav>
        </div>
      </header>

      <section className="hero">
        <div className="container">
          <h1>Your Personality.<br />Bottled</h1>
          <p style={{ color: 'white', maxWidth: '500px' }}>From mood to muse, discover your scented self</p>
          <Link href="#explore" className="cta-button">
            Start Exploring
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </Link>
        </div>
      </section>

      <section className="how-it-works" id="howitworks">
        <div className="container">
          <h2>How It Works</h2>
          <div className="dotted-line"></div>

          <div className="step">
            <div className="step-image">
              <Image src="/work1.png" alt="Profile You" width={240} height={240} />
            </div>
            <div className="step-content">
              <div className="step-number">#1 Profile You</div>
              <p>Share your personality traits, MBTI type, and zodiac sign to help our system understand your unique essence and fragrance preferences.</p>
            </div>
          </div>

          <div className="step">
            <div className="step-image">
              <Image src="/work2.png" alt="Share Inspirations" width={240} height={240} />
            </div>
            <div className="step-content">
              <div className="step-number">#2 Share Inspirations</div>
              <p>Tell us which celebrities, characters, or icons inspire you, giving us insight into your style and aesthetic preferences.</p>
            </div>
          </div>

          <div className="step">
            <div className="step-image">
              <Image src="/work3.png" alt="Smart Match" width={240} height={240} />
            </div>
            <div className="step-content">
              <div className="step-number">#3 Smart Match</div>
              <p>Our algorithm analyzes your inputs to identify fragrance families and notes that perfectly complement your personality profile.</p>
            </div>
          </div>

          <div className="step">
            <div className="step-image">
              <Image src="/work4.png" alt="Custom Scent" width={240} height={240} />
            </div>
            <div className="step-content">
              <div className="step-number">#4 Custom Scent</div>
              <p>Receive personalized fragrance recommendations or create your own bespoke scent formula tailored to your unique profile.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="features" id="features">
        <div className="container">
          <h2>Our feature</h2>

          <div className="feature-grid">
            <div className="feature-card">
              <h3>Personality Match System</h3>
              <div className="feature-number">01</div>
            </div>

            <div className="feature-card">
              <h3>Celebrity Scent Library</h3>
              <div className="feature-number">02</div>
            </div>

            <div className="feature-card">
              <h3>Bespoke Fragrance Lab</h3>
              <div className="feature-number">03</div>
            </div>
          </div>
        </div>
      </section>

      <section className="testimonials" id="blog">
        <div className="container">
          <h2>User Feedback</h2>
          <p className="testimonials-subtitle">"What our customers are saying"</p>

          <div className="testimonial-slider">
            <div className="testimonial-slide">
              <div className="testimonial-quote">"</div>
              <p className="testimonial-text">{testimonials[currentSlide].text}</p>
              <div className="testimonial-author">
                <div className="author-avatar"></div>
                <div className="author-info">
                  <h4>{testimonials[currentSlide].author}</h4>
                  <p>{testimonials[currentSlide].age}</p>
                </div>
              </div>
            </div>

            <div className="slider-nav">
              <button className="prev" onClick={prevSlide}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M15 18L9 12L15 6" stroke="#9174cb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
              <button className="next" onClick={nextSlide}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 18L15 12L9 6" stroke="#9174cb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </section>

      <section className="faq" id="FAQ">
        <div className="container">
          <h2>FAQ</h2>

          <div className="faq-list">
            <div className="faq-item">
              <div className="faq-question">
                <div className="faq-icon">?</div>
                <h3>How do I create my first scent profile?</h3>
              </div>
              <div className="faq-answer">
                <p>Simply click the "Start Exploring" button, fill out the personal questionnaire, share your preferences and sources of inspiration, and our system will instantly generate a personalized scent recommendation for you.</p>
              </div>
            </div>

            <div className="faq-item">
              <div className="faq-question">
                <div className="faq-icon">?</div>
                <h3>Do I need to create an account to use Fragrance Inspo?</h3>
              </div>
              <div className="faq-answer">
                <p>An account is not required for basic recommendations, but creating an account allows you to save your scent profile, keep track of your favorite fragrances, and gain access to more personalized features.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer id="about">
        <div className="container">
          <p>&copy; {new Date().getFullYear()} Your Personality. Bottled </p>
        </div>
      </footer>
    </div>
  );
}