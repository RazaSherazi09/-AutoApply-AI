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
          relative flex flex-col items-center justify-center p-12 md:p-16 rounded-3xl border-2 border-dashed
          cursor-pointer overflow-hidden transition-all duration-300 min-h-[280px]
          ${isDragging ? 'border-[#06b6d4] bg-[#06b6d4]/5 scale-[1.02]' : 'border-white/10 bg-[#0f0f23]/50 hover:border-[#8b5cf6]/40 hover:bg-white/5'}
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

        <div className={`w-20 h-20 rounded-full flex items-center justify-center mb-6 transition-colors duration-500 shadow-xl
          ${isDragging ? 'bg-gradient-to-br from-[#06b6d4] to-[#8b5cf6] text-white shadow-[0_0_30px_rgba(6,182,212,0.3)]' : 'bg-[#0a0a0f] border border-white/5 group-hover:bg-white/5 text-[#06b6d4]'}`}
        >
          {uploading ? (
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-current" />
          ) : (
            <UploadCloud size={32} />
          )}
        </div>

        <h3 className="font-sans text-xl font-medium text-white mb-2 text-center">
          {uploading ? "Analyzing document..." : "Drop your resume here or click to upload"}
        </h3>
        <p className="text-[#a39f98] text-sm">PDF formats only. Strict privacy maintained.</p>
        
        {uploadResult && (
          <div className={`absolute bottom-6 font-medium text-sm flex items-center gap-2 px-4 py-2 rounded-full border bg-[#0a0a0f]/80 backdrop-blur ${uploadResult.includes('✅') ? 'text-green-400 border-green-500/20' : 'text-red-400 border-red-500/20'}`}>
            {uploadResult}
          </div>
        )}
      </div>
    </motion.div>
  );
}
