import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({ children, className = '', onClick }) => {
  const baseStyles = 'bg-white rounded-lg shadow-md p-6';
  const interactiveStyles = onClick ? 'cursor-pointer hover:shadow-lg transition-shadow duration-200' : '';

  return (
    <div className={`${baseStyles} ${interactiveStyles} ${className}`} onClick={onClick}>
      {children}
    </div>
  );
};
