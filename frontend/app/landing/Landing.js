'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import styles from './Landing.module.css';
import MainLayout from '../MainLayout';

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
    <MainLayout>
      <section className={styles.hero}>
        <div className={styles.container}>
          <h1>Your Personality.<br />Bottled</h1>
          <p style={{ color: 'white', maxWidth: '500px' }}>From mood to muse, discover your scented self</p>
          <Link href="/chat" className={styles.ctaButton}>
            Start Exploring
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </Link>
        </div>
      </section>

      <section className={styles.howItWorks} id="howitworks">
        <div className={styles.container}>
          <h2>How It Works</h2>
          <div className={styles.dottedLine}></div>

          <div className={styles.step}>
            <div className={styles.stepImage}>
              <Image src="/work1.png" alt="Profile You" width={240} height={240} />
            </div>
            <div className={styles.stepContent}>
              <div className={styles.stepNumber}>#1 Profile You</div>
              <p>Share your personality traits, MBTI type, and zodiac sign to help our system understand your unique essence and fragrance preferences.</p>
            </div>
          </div>

          <div className={styles.step}>
            <div className={styles.stepImage}>
              <Image src="/work2.png" alt="Share Inspirations" width={240} height={240} />
            </div>
            <div className={styles.stepContent}>
              <div className={styles.stepNumber}>#2 Share Inspirations</div>
              <p>Tell us which celebrities, characters, or icons inspire you, giving us insight into your style and aesthetic preferences.</p>
            </div>
          </div>

          <div className={styles.step}>
            <div className={styles.stepImage}>
              <Image src="/work3.png" alt="Smart Match" width={240} height={240} />
            </div>
            <div className={styles.stepContent}>
              <div className={styles.stepNumber}>#3 Smart Match</div>
              <p>Our algorithm analyzes your inputs to identify fragrance families and notes that perfectly complement your personality profile.</p>
            </div>
          </div>

          <div className={styles.step}>
            <div className={styles.stepImage}>
              <Image src="/work4.png" alt="Custom Scent" width={240} height={240} />
            </div>
            <div className={styles.stepContent}>
              <div className={styles.stepNumber}>#4 Custom Scent</div>
              <p>Receive personalized fragrance recommendations or create your own bespoke scent formula tailored to your unique profile.</p>
            </div>
          </div>
        </div>
      </section>

      <section className={styles.features} id="features">
        <div className={styles.container}>
          <h2>Our feature</h2>

          <div className={styles.featureGrid}>
            <div className={styles.featureCard}>
              <h3>Personality Match System</h3>
              <div className={styles.featureNumber}>01</div>
            </div>

            <div className={styles.featureCard}>
              <h3>Celebrity Scent Library</h3>
              <div className={styles.featureNumber}>02</div>
            </div>

            <div className={styles.featureCard}>
              <h3>Bespoke Fragrance Lab</h3>
              <div className={styles.featureNumber}>03</div>
            </div>
          </div>
        </div>
      </section>

      <section className={styles.testimonials} id="blog">
        <div className={styles.container}>
          <h2>User Feedback</h2>
          <p className={styles.testimonialsSubtitle}>"What our customers are saying"</p>

          <div className={styles.testimonialSlider}>
            <div className={styles.testimonialSlide}>
              <div className={styles.testimonialQuote}>"</div>
              <p className={styles.testimonialText}>{testimonials[currentSlide].text}</p>
              <div className={styles.testimonialAuthor}>
                <div className={styles.authorAvatar}></div>
                <div className={styles.authorInfo}>
                  <h4>{testimonials[currentSlide].author}</h4>
                  <p>{testimonials[currentSlide].age}</p>
                </div>
              </div>
            </div>

            <div className={styles.sliderNav}>
              <button className={styles.prev} onClick={prevSlide}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M15 18L9 12L15 6" stroke="#9174cb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
              <button className={styles.next} onClick={nextSlide}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 18L15 12L9 6" stroke="#9174cb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </section>

      <section className={styles.faq} id="FAQ">
        <div className={styles.container}>
          <h2>FAQ</h2>

          <div className={styles.faqList}>
            <div className={styles.faqItem}>
              <div className={styles.faqQuestion}>
                <div className={styles.faqIcon}>?</div>
                <h3>How do I create my first scent profile?</h3>
              </div>
              <div className={styles.faqAnswer}>
                <p>Simply click the "Start Exploring" button, fill out the personal questionnaire, share your preferences and sources of inspiration, and our system will instantly generate a personalized scent recommendation for you.</p>
              </div>
            </div>

            <div className={styles.faqItem}>
              <div className={styles.faqQuestion}>
                <div className={styles.faqIcon}>?</div>
                <h3>Do I need to create an account to use Fragrance Inspo?</h3>
              </div>
              <div className={styles.faqAnswer}>
                <p>An account is not required for basic recommendations, but creating an account allows you to save your scent profile, keep track of your favorite fragrances, and gain access to more personalized features.</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </MainLayout>
  );
}