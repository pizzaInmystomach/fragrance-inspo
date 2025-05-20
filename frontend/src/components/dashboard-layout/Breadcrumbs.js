import React from 'react';
import Link from 'next/link';
import styles from './Breadcrumbs.module.css';

function Breadcrumbs({ items }) {
  return (
    <nav className={styles.breadcrumbs}>
      {items.map((item, index) => (
        <React.Fragment key={item.label}>
          {item.href ? (
            <Link href={item.href} className={styles.breadcrumbLink}>
              {item.label}
            </Link>
          ) : (
            <span className={styles.breadcrumbCurrent}>{item.label}</span>
          )}
          {index < items.length - 1 && <span className={styles.separator}>/</span>}
        </React.Fragment>
      ))}
    </nav>
  );
}

export default Breadcrumbs;