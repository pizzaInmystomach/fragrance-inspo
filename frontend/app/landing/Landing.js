'use client'

import { useState } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import styles from './Landing.module.css'
import MainLayout from '../MainLayout'
import GoogleLoginButton from 'src/components/GoogleLoginButton.js'

export default function Landing() {
  const [currentSlide, setCurrentSlide] = useState(0)

  const testimonials = [
    {
      text: "Incredibly accurate! The fragrance the system recommended feels genuinely 'me'.",
      author: "Emily K.",
      age: "32",
    },
    {
      text: "The personality matching system is brilliant. I've found my signature scent!",
      author: "James T.",
      age: "28",
    },
    {
      text: "I was skeptical at first, but the recommended fragrance perfectly captures my essence.",
      author: "Sophia R.",
      age: "35",
    },
  ]

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev === 0 ? testimonials.length - 1 : prev - 1))
  }

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev === testimonials.length - 1 ? 0 : prev + 1))
  }

  return (
    <MainLayout>
      {/* === Hero 區塊 === */}
      <section className={styles.hero}>
        <div className={styles.container}>
          <h1>Your Personality.<br />Bottled</h1>
          <p style={{ color: 'white', maxWidth: '500px' }}>
            From mood to muse, discover your scented self
          </p>
          <Link href="/chat" className={styles.ctaButton}>
            Start Exploring
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M5 12H19M19 12L12 5M19 12L12 19"
                stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </Link>

          {/* 登入按鈕加在 Hero 區底下 */}
          <div style={{ marginTop: '30px' }}>
            <GoogleLoginButton />
          </div>
        </div>
      </section>

      {/* === How It Works 區塊 === */}
      <section className={styles.howItWorks} id="howitworks">
        <div className={styles.container}>
          <h2>How It Works</h2>
          <div className={styles.dottedLine}></div>
          {/* 3 Steps */}
          {[1, 2, 3].map((step, index) => (
            <div className={styles.step} key={step}>
              <div className={styles.stepImage}>
                <Image
                  src={`https://yourcdn.com/images/work${step}.png`}
                  alt={`Step ${step}`}
                  width={240}
                  height={240}
                  unoptimized
                />
              </div>
              <div className={styles.stepContent}>
                <div className={styles.stepNumber}># Step {step}</div>
                <p>
                  {[
                    'Enter the name of a celebrity or character you\'re interested in.',
                    'The system will recommend a selection of perfumes that reflect their personality.',
                    'Add your preferred scents to your personal library for future reference.',
                  ][index]}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* === Feature 區塊 === */}
      <section className={styles.features} id="features">
        <div className={styles.container}>
          <h2>Our feature</h2>
          <div className={styles.featureGrid}>
            {['Celebrity scent recommendation', 'Character scent recommendation', 'Scent Library'].map((title, index) => (
              <div className={styles.featureCard} key={index}>
                <h3>{title}</h3>
                <div className={styles.featureNumber}>0{index + 1}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* === Testimonials 區塊 === */}
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
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M15 18L9 12L15 6" stroke="#9174cb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
              <button className={styles.next} onClick={nextSlide}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M9 18L15 12L9 6" stroke="#9174cb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* === FAQ 區塊 === */}
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
                <p>
                  Simply click the "Start Exploring" button, fill out the personal questionnaire, share your preferences and sources of inspiration, and our system will instantly generate a personalized scent recommendation for you.
                </p>
              </div>
            </div>

            <div className={styles.faqItem}>
              <div className={styles.faqQuestion}>
                <div className={styles.faqIcon}>?</div>
                <h3>Do I need to create an account to use Fragrance Inspo?</h3>
              </div>
              <div className={styles.faqAnswer}>
                <p>
                  An account is not required for basic recommendations, but creating an account allows you to save your scent profile, keep track of your favorite fragrances, and gain access to more personalized features.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </MainLayout>
  )
}
