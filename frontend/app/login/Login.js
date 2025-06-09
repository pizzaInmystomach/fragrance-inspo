'use client';

import { useState } from 'react';
import styles from './Login.module.css';
import GoogleLoginButton from '@/components/GoogleLoginButton';
import DynamicBlobsBackground from '@/components/main-layout/DynamicBlobs';

export default function LoginPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    // Simulate login process
    setTimeout(() => {
      setIsLoading(false);
      console.log('Login attempt:', formData);
    }, 1500);
  };

  return (
    <div className={styles.container}>
      <DynamicBlobsBackground>
      {/* Main Content */}
      <main className={styles.main}>
        <div className={styles.loginSection}>
          <div className={styles.loginContainer}>
            <div className={styles.loginContent}>
            <div className={styles.logo}>
                <div className={styles.logoIcon}></div>
                <span>Scented</span>
            </div>
              <h1 className={styles.title}>Welcome Back</h1>
              <p className={styles.subtitle}>
                Sign in to continue your scented journey
              </p>

              <form onSubmit={handleSubmit} className={styles.form}>
                <GoogleLoginButton />
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
                    placeholder="Enter your password"
                    required
                  />
                </div>

                <div className={styles.formOptions}>
                  <label className={styles.checkbox}>
                    <input type="checkbox" />
                    <span className={styles.checkmark}></span>
                    Remember me
                  </label>
                  <a href="/forgot-password" className={styles.forgotLink}>
                    Forgot password?
                  </a>
                </div>

                <button 
                  type="submit" 
                  className={styles.submitButton}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <span className={styles.loading}>Signing in...</span>
                  ) : (
                    <>
                      Sign In
                      <span className={styles.arrow}>→</span>
                    </>
                  )}
                </button>
              </form>

              <div className={styles.divider}>
                <span>or continue with</span>
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

              <p className={styles.signupLink}>
                Don't have an account?{' '}
                <a href="/signup">Create one here</a>
              </p>
            </div>
          </div>

          <div className={styles.illustrationSection}>
            <div className={styles.illustration}>
              <div className={styles.perfumeBottle}>
                <div className={styles.bottleBody}></div>
                <div className={styles.bottleTop}></div>
                <div className={styles.bottleLabel}></div>
              </div>
              <div className={styles.sparkles}>
                <div className={styles.sparkle}></div>
                <div className={styles.sparkle}></div>
                <div className={styles.sparkle}></div>
              </div>
            </div>
            <div className={styles.illustrationText}>
              <h3>Your Scented Story Awaits</h3>
              <p>Discover fragrances that match your unique personality</p>
            </div>
          </div>
        </div>
      </main>
      </DynamicBlobsBackground>
    </div>
  );
}