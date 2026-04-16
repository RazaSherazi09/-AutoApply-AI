"use client";

import { motion } from "framer-motion";
import { UploadCloud } from "lucide-react";
import { useState, useRef } from "react";

interface UploadDropzoneProps {
  onUpload: (file: File) => Promise<void>;
  uploading: boolean;
  uploadResult: string | null;
}

export default function UploadDropzone({ onUpload, uploading, uploadResult }: UploadDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) onUpload(file);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }} 
      animate={{ opacity: 1, y: 0 }} 
      transition={{ duration: 0.5 }}
      className="mb-12"
    >
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`
          relative flex flex-col items-center justify-center p-12 md:p-16 border-2 border-dashed
          cursor-pointer overflow-hidden transition-all duration-150 min-h-[280px]
          ${isDragging ? 'border-[var(--accent)] bg-[var(--accent)]/5' : 'border-[var(--border)] hover:border-[var(--border-hover)] bg-transparent'}
          ${uploading ? 'pointer-events-none opacity-50' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onUpload(file);
          }}
        />

        <div className={`w-16 h-16 flex items-center justify-center mb-6 border transition-colors duration-150
          ${isDragging ? 'border-[var(--accent)] text-[var(--accent)]' : 'border-[var(--border)] text-[var(--muted-fg)]'}`}
        >
          {uploading ? (
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[var(--accent)]" />
          ) : (
            <UploadCloud size={28} strokeWidth={1.5} />
          )}
        </div>

        <h3 className="text-xl md:text-2xl font-bold text-[var(--foreground)] mb-2 text-center tracking-tight" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.04em' }}>
          {uploading ? "Analyzing document..." : "Drop your resume here"}
        </h3>
        <p className="text-[var(--muted-fg)] text-sm uppercase tracking-[0.1em]" style={{ fontFamily: 'var(--font-mono)' }}>PDF format — strict privacy</p>
        
        {uploadResult && (
          <div className={`absolute bottom-6 font-mono text-sm flex items-center gap-2 px-4 py-2 border ${uploadResult.includes('✅') ? 'text-[var(--success)] border-[var(--success)]' : 'text-[var(--error)] border-[var(--error)]'}`}>
            {uploadResult}
          </div>
        )}
      </div>
    </motion.div>
  );
}
