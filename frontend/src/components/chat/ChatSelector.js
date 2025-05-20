import React, { useState } from 'react';
import styles from './ChatSelector.module.css';

function ChatSelector({ 
  options, 
  onSelect, 
  title = 'Select the description that best matches', 
}) {
  const [selectedOption, setSelectedOption] = useState(null);

  const handleOptionSelect = (option) => {
    setSelectedOption(option);
    onSelect(option);
  };

  return (
    <div className={styles.selectorContainer}>
      <h3 className={styles.selectorTitle}>{title}</h3>
      <div className={styles.optionsGrid}>
        {options.map((option) => (
          <button
            key={option.id}
            className={`${styles.optionButton} ${selectedOption?.id === option.id ? styles.selected : ''}`}
            onClick={() => handleOptionSelect(option)}
          >
            {option.icon && <span className={styles.optionIcon}>{option.icon}</span>}
            <span className={styles.optionLabel}>{option.label}</span>
            <span className={styles.optionDescription}>{option.description}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default ChatSelector;