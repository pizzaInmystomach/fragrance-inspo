'use client';

import { useState } from 'react';
import styles from './SignUp.module.css';
import DynamicBlobsBackground from '@/components/main-layout/DynamicBlobs';

export default function SignupPage() {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!acceptTerms) {
      alert('Please accept the terms and conditions');
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      alert('Passwords do not match');
      return;
    }
    
    setIsLoading(true);
    
    // Simulate signup process
    setTimeout(() => {
      setIsLoading(false);
      console.log('Signup attempt:', formData);
    }, 2000);
  };

  return (
    <div className={styles.container}>
      <DynamicBlobsBackground>
      {/* Main Content */}
      <main className={styles.main}>
        <div className={styles.signupSection}>
          <div className={styles.signupContainer}>
            <div className={styles.signupContent}>
              <div className={styles.header}>
                <h1 className={styles.title}>Create Your Account</h1>
                <p className={styles.subtitle}>
                  Join us and discover your perfect scent
                </p>
              </div>

              <form onSubmit={handleSubmit} className={styles.form}>
                <div className={styles.nameRow}>
                  <div className={styles.inputGroup}>
                    <label htmlFor="firstName" className={styles.label}>
                      First Name
                    </label>
                    <input
                      type="text"
                      id="firstName"
                      name="firstName"
                      value={formData.firstName}
                      onChange={handleChange}
                      className={styles.input}
                      placeholder="Your first name"
                      required
                    />
                  </div>

                  <div className={styles.inputGroup}>
                    <label htmlFor="lastName" className={styles.label}>
                      Last Name
                    </label>
                    <input
                      type="text"
                      id="lastName"
                      name="lastName"
                      value={formData.lastName}
                      onChange={handleChange}
                      className={styles.input}
                      placeholder="Your last name"
                      required
                    />
                  </div>
                </div>

                <div className={styles.inputGroup}>
                  <label htmlFor="email" className={styles.label}>
                    Email Address
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className={styles.input}
                    placeholder="Enter your email"
                    required
                  />
                </div>

                <div className={styles.inputGroup}>
                  <label htmlFor="password" className={styles.label}>
                    Password
                  </label>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    className={styles.input}
                    placeholder="Create a strong password"
                    required
                  />
                  <div className={styles.passwordHint}>
                    At least 8 characters with numbers and symbols
                  </div>
                </div>

                <div className={styles.inputGroup}>
                  <label htmlFor="confirmPassword" className={styles.label}>
                    Confirm Password
                  </label>
                  <input
                    type="password"
                    id="confirmPassword"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className={styles.input}
                    placeholder="Confirm your password"
                    required
                  />
                </div>

                <div className={styles.termsSection}>
                  <label className={styles.checkbox}>
                    <input 
                      type="checkbox" 
                      checked={acceptTerms}
                      onChange={(e) => setAcceptTerms(e.target.checked)}
                    />
                    <span className={styles.checkmark}></span>
                    I agree to the{' '}
                    <a href="/terms" className={styles.link}>Terms of Service</a>
                    {' '}and{' '}
                    <a href="/privacy" className={styles.link}>Privacy Policy</a>
                  </label>
                </div>

                <button 
                  type="submit" 
                  className={styles.submitButton}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <span className={styles.loading}>Creating Account...</span>
                  ) : (
                    <>
                      Create Account
                      <span className={styles.arrow}>→</span>
                    </>
                  )}
                </button>
              </form>

              <div className={styles.divider}>
                <span>or sign up with</span>
              </div>

              <div className={styles.socialButtons}>
                <button className={styles.socialButton}>
                  <span className={styles.googleIcon}>G</span>
                  Google
                </button>
                <button className={styles.socialButton}>
                  <span className={styles.appleIcon}>🍎</span>
                  Apple
                </button>
              </div>

              <p className={styles.loginLink}>
                Already have an account?{' '}
                <a href="/login">Sign in here</a>
              </p>
            </div>
          </div>

          <div className={styles.illustrationSection}>
            <div className={styles.illustration}>
              <div className={styles.perfumeCollection}>
                <div className={styles.bottle1}>
                  <div className={styles.bottleBody}></div>
                  <div className={styles.bottleTop}></div>
                </div>
                <div className={styles.bottle2}>
                  <div className={styles.bottleBody}></div>
                  <div className={styles.bottleTop}></div>
                </div>
                <div className={styles.bottle3}>
                  <div className={styles.bottleBody}></div>
                  <div className={styles.bottleTop}></div>
                </div>
              </div>
              <div className={styles.floatingElements}>
                <div className={styles.heart}></div>
                <div className={styles.star}></div>
                <div className={styles.circle}></div>
                <div className={styles.sparkles}>
                  <div className={styles.sparkle}></div>
                  <div className={styles.sparkle}></div>
                  <div className={styles.sparkle}></div>
                  <div className={styles.sparkle}></div>
                </div>
              </div>
            </div>
            <div className={styles.illustrationText}>
              <h3>Begin Your Scented Journey</h3>
              <p>Discover fragrances that tell your unique story and express your personality</p>
            </div>
          </div>
        </div>
      </main>
      </DynamicBlobsBackground>
    </div>
  );
}