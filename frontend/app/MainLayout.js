import styles from './MainLayout.module.css';
import Header from "@/components/main-layout/header";
import Footer from '@/components/main-layout/Footer';

export default function MainLayout({ children }) {
  return (
    <main className={styles.main}>
        <Header />
        {children}
        <Footer />
    </main>
  );
}