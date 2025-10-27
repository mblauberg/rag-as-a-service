import React from 'react';
import { FileText, FileType, Table, FileCode, File } from 'lucide-react';
import { cn } from '@/lib/utils';

export type FileIconType = 'pdf' | 'docx' | 'doc' | 'txt' | 'csv' | 'md' | 'markdown' | 'default';

interface FileIconProps {
  type: FileIconType;
  className?: string;
}

/** FileIcon - Renders appropriate icon based on file type. */
export const FileIcon: React.FC<FileIconProps> = ({ type, className }) => {
  const iconClass = cn('w-6 h-6', className);

  switch (type) {
    case 'pdf':
    case 'txt':
      return <FileText className={iconClass} />;
    case 'docx':
    case 'doc':
      return <FileType className={iconClass} />;
    case 'csv':
      return <Table className={iconClass} />;
    case 'md':
    case 'markdown':
      return <FileCode className={iconClass} />;
    default:
      return <File className={iconClass} />;
  }
};
