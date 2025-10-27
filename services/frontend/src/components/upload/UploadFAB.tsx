import React from 'react';
import { PlusIcon } from '@radix-ui/react-icons';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';

interface UploadFABProps {
  onClick: () => void;
}

/** Floating Action Button for document uploads. */
export const UploadFAB: React.FC<UploadFABProps> = ({ onClick }) => {
  return (
    <motion.div
      className="fixed bottom-8 right-8 z-50"
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ type: "spring", stiffness: 260, damping: 20 }}
    >
      <Button
        onClick={onClick}
        className="h-14 w-14 rounded-full shadow-lg hover:shadow-xl transition-shadow"
        aria-label="Upload document"
      >
        <PlusIcon className="h-6 w-6" />
      </Button>
    </motion.div>
  );
};
