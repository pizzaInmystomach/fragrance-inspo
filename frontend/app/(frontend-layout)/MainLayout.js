import styles from './MainLayout.module.css';
import Header from "@/components/main-layout/Header";
import Footer from '@/components/main-layout/Footer';
import BouncingBlobs from '@/components/main-layout/Blobs';
import DynamicBlobsBackground from '@/components/main-layout/DynamicBlobs'

export default function MainLayout({ children }) {
  return (
        <main className={styles.main}>
          <DynamicBlobsBackground>
          <Header />
          <div className={styles.content}>
            {children}
          </div>
          <Footer />
        </DynamicBlobsBackground>
        </main>
  );
}
