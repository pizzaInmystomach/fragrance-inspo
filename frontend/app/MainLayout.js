import styles from './MainLayout.module.css';
import Header from "@/components/main-layout/Header";
import Footer from '@/components/main-layout/Footer';
import BouncingBlobs from '@/components/main-layout/Blobs';

export default function MainLayout({ children }) {
  return (
    <main className={styles.main}>
        <Header />
        {children}
        <Footer />
        {children}
        <BouncingBlobs />
    
    </main>
  );
}