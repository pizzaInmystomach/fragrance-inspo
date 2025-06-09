'use client'

import { useState } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import styles from './Landing.module.css'
import GoogleLoginButton from '@/components/GoogleLoginButton.js';
import { FaQuoteLeft } from "react-icons/fa6";
import { Card, CardContent } from "@/components/ui/card"
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel"

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
    <>
      {/* === Hero 區塊 === */}
      <section className={styles.hero}>
        <div className={styles.container}>
          <h1>Your Personality.<br />Bottled</h1>
          <div className={styles.cta}>
            <Link href="/chat" className={styles.ctaButton}>
              <p>Start Exploring</p>
              <svg width="25" height="25" viewBox="0 0 24 24" fill="none">
                <path d="M5 12H19M19 12L12 5M19 12L12 19"
                  stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </Link>
            <div className={styles.ctaText}>
              <p><span>F</span>rom mood to muse...</p>
              <p><span>D</span>iscover your scented self</p>
            </div>
            
          </div>
          

          {/* 登入按鈕加在 Hero 區底下 */}
          <div style={{ marginTop: '30px' }}>
            <GoogleLoginButton />
          </div>
        </div>
      </section>

      {/* === How It Works 區塊 === */}
      <section className={`${styles.section} ${styles.howItWorks}`} id="howitworks">
        <div className={styles.container}>
          <h2>How It Works</h2>
          {/* 3 Steps */}
          <div className={styles.stepsContainer}>
            <div className={styles.stepsContent}>
              <div className={styles.stepContentText}>
                <h3><span>#1</span>Step 1 - Profile You</h3>
                <p>Enter the name of a celebrity or character you're interested in.</p>
              </div>
              <div className={styles.stepContentImage}>
                <Image
                  src="/how-it-works01.png"
                  alt="Step 1"
                  width={320}
                  height={320}                 
                  unoptimized
                />
              </div>
              <div className={styles.dottedLine}>
                <svg width="1200" height="400" xmlns="http://www.w3.org/2000/svg">
                  <g transform="translate(80, 50)">
                    <path d="M 0 0
                              L 0 120
                              Q 0 160 40 160
                              L 400 160
                              Q 480 160 480 200
                              L 480 360" 
                          stroke="#fff" 
                          stroke-width="3" 
                          stroke-dasharray="8,4"
                          fill="none" 
                          stroke-linecap="round"/>
                  </g>
                </svg>
              </div>
            </div>
            <div className={styles.stepsContent}>
              <div className={styles.stepContentImage}>
                <Image
                  src="/how-it-works02.png"
                  alt="Step 1"
                  width={320}
                  height={320}                  
                  unoptimized
                />
              </div>
              <div className={styles.stepContentText} style={{ flexBasis: '59%'}}>
                <h3><span>#2</span>Step 2</h3>
                <p>Enter the name of a celebrity or character you're interested in.</p>
              </div>
              <div className={styles.dottedLineScaleX}>
                <svg width="1200" height="400" xmlns="http://www.w3.org/2000/svg">
                  <g transform="translate(80, 50)">
                    <path d="M 0 0
                            L 0 180
                            Q 0 220 40 220
                            L 400 220
                            Q 480 220 480 260
                            L 480 460" 
                          stroke="#fff" 
                          stroke-width="3" 
                          stroke-dasharray="8,4"
                          fill="none" 
                          stroke-linecap="round"
                    />
                  </g>
                </svg>
              </div>
            </div>
            <div className={styles.stepsContent} style={{ marginTop: '50px'}}>
              <div className={styles.stepContentText}>
                <h3><span>#1</span>Profile You</h3>
                <p>Enter the name of a celebrity or character you're interested in.</p>
              </div>
              <div className={styles.stepContentImage}>
                <Image
                  src="/how-it-works03.png"
                  alt="Step 1"
                  width={320}
                  height={320}                  
                  unoptimized
                />
              </div>
            </div>
          </div>
        </div>
        
      </section>

      {/* === Feature 區塊 === */}
      <section className={styles.section} id="features">
        <div className={styles.container}>
          <h2>Our features</h2>
          <div className={styles.featureGrid}>
            {['Celebrity scent recommendation', 'Character scent recommendation', 'Scent Library'].map((title, index) => (
              <div className={styles.featureCard} key={index}>
                <h5>{title}</h5>
                <div className={styles.featureNumber}>0{index + 1}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* === Testimonials 區塊 === */}
      <section className={`${styles.section} ${styles.testimonials}`} id="blog">
        <div className={styles.container}>
          <h2>User Feedback</h2>
          <div className={styles.testimonialsContents}>
            <div className={styles.testimonialsSubtitle}>
              <FaQuoteLeft color='white' size={50}/>
              <p>What our customers are saying</p>
            </div>
            <CarouselSize />

            {/* <div className={styles.testimonialSlider}>
              <div className={styles.testimonialSlide}>
                <div className={styles.testimonialQuote}>
                  <FaQuoteLeft color='#ffffffcc' size={36}/>
                </div>
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
            </div> */}
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
    </>
  )
}

export function CarouselSize() {
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
    {
      text: "I've been using this service for a few months now and it's been a game-changer!",
      author: "Daniel M.",
      age: "30",
    },
    {
      text: "I can't believe how accurate the system is. It's like having a personal stylist.",
      author: "Olivia C.",
      age: "27",
    },
    {
      text: "I'm blown away by the accuracy of the system. It's like having a personal stylist.",
      author: "Liam H.",
      age: "29",
    },
  ]
  return (
    <Carousel
      opts={{
        align: "start",
      }}
      className={styles.testimonialSlider}
    >
      <CarouselContent>
        {testimonials.map((testimonial, index) => (
          <CarouselItem key={index} className="md:basis-1/2 lg:basis-1/3">
            <div className="p-1">
              <Card className={styles.testimonialCard}>
                <CardContent className={`${styles.testimonialCardContent}`}>
                    <FaQuoteLeft size={36} color='#ffffffcc' />
                    <p className="text-center text-sm leading-6">{testimonial.text}</p>
                    <div className={styles.testimonialAuthor}>
                      <div className={styles.authorAvatar}></div>
                      <div className={styles.authorInfo}>
                        <p>{testimonial.author}</p>
                        <p>{testimonial.age}</p>
                      </div>
                    </div>
                </CardContent>
              </Card>
            </div>
          </CarouselItem>
        ))}
      </CarouselContent>
      <CarouselPrevious />
      <CarouselNext />
    </Carousel>
  )
}
