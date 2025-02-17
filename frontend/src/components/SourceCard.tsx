import React from 'react';
import { ExternalLink } from 'lucide-react';
import { Source } from '../types';

interface SourceCardProps {
  source: Source;
}

export const SourceCard: React.FC<SourceCardProps> = ({ source }) => {
  return (
    <div className="mb-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-all duration-200 hover:shadow-md hover:translate-y-[-2px] animate-fade-in">
      <p className="mb-2 line-clamp-3 text-sm text-gray-600">{source.text}</p>
      <a
        href={source.url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1 text-sm text-blue-500 transition-colors duration-200 hover:text-blue-700"
      >
        <ExternalLink className="h-4 w-4 transition-transform group-hover:scale-110" />
        View Source
      </a>
    </div>
  );
};