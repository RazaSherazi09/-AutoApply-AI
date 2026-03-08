"use client";

import { useEffect, useState } from "react";
import { resumesApi, type Resume } from "@/lib/api";
import { motion } from "framer-motion";
import { FileText, CheckCircle2 } from "lucide-react";
import PageContainer from "@/components/PageContainer";
import UploadDropzone from "@/components/UploadDropzone";
import GlassCard from "@/components/GlassCard";

export default function ResumesPage() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<string | null>(null);

  async function loadResumes() {
    try {
      const data = await resumesApi.list("?limit=20");
      setResumes(data.items);
      setTotal(data.total);
    } catch { } finally { setLoading(false); }
  }

  useEffect(() => { loadResumes(); }, []);

  const handleUpload = async (file: File) => {
    if (file.type !== "application/pdf") {
      setUploadResult("❌ Only PDF files are supported.");
      return;
    }
    setUploading(true);
    setUploadResult(null);
    try {
      const result = await resumesApi.upload(file);
      setUploadResult(`✅ Document v${result.version} analyzed and integrated.`);
      await loadResumes();
    } catch (err: unknown) {
      setUploadResult(`❌ ${err instanceof Error ? err.message : "Upload failed"}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this resume? This action cannot be undone.")) return;
    
    try {
      await resumesApi.delete(id);
      await loadResumes();
    } catch (err: unknown) {
      alert(`Delete failed: ${err instanceof Error ? err.message : "Unknown error"}`);
    }
  };

  const parseData = (raw: string) => {
    try { return JSON.parse(raw); } catch { return {}; }
  };

  return (
    <PageContainer>
      <header className="mb-12">
        <motion.h1 
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} 
          className="page-title mb-2"
        >
          Candidate Documents
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          className="text-[#a39f98]"
        >
          Maintain your dossier. Documents are securely digitized into matching vectors.
        </motion.p>
      </header>

      {/* Drag & Drop Component */}
      <UploadDropzone 
        onUpload={handleUpload}
        uploading={uploading}
        uploadResult={uploadResult}
      />

      {/* Existing Resumes */}
      <motion.div 
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
      >
        <h2 className="text-xl font-semibold tracking-wide text-white mb-8 flex items-center justify-between border-b border-white/5 pb-4">
          <span>Dossier Archive</span>
          <span className="text-sm font-sans tracking-widest text-[#a39f98] font-semibold">{total} Files</span>
        </h2>

        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[#06b6d4]" />
          </div>
        ) : resumes.length === 0 ? (
          <div className="text-center py-20 border border-white/5 rounded-2xl bg-[#0a0a0f]/50">
            <p className="text-[#a39f98] font-sans text-lg mb-2 font-medium">Archive empty.</p>
            <p className="text-sm text-[#a39f98]/60">Upload your PDF resume to begin matching and applying.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {resumes.map((r, i) => {
              const data = parseData(r.structured_data || "{}");
              return (
                <motion.div
                  key={r.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 * i, duration: 0.4 }}
                >
                  <GlassCard className="flex flex-col h-full hover:border-[#06b6d4]/20 group">
                    <div className="flex items-start justify-between mb-6">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-[#0a0a0f] flex items-center justify-center text-[#06b6d4] border border-white/5 shadow-inner">
                          <FileText size={20} />
                        </div>
                        <div>
                          <h4 className="font-sans font-semibold text-lg text-white group-hover:text-[#06b6d4] transition-colors line-clamp-1">{r.file_name}</h4>
                          <p className="text-xs font-medium text-[#a39f98] uppercase tracking-wider mt-1">Version {r.version} • {new Date(r.created_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <span className="badge badge-primary bg-[#06b6d4]/10 text-[#06b6d4] border-[#06b6d4]/20 flex items-center gap-1.5 px-3 py-1">
                          <CheckCircle2 size={12} className="shrink-0" /> <span className="pt-px tracking-wider">Active</span>
                        </span>
                        <button 
                          onClick={() => handleDelete(r.id)}
                          className="text-[10px] font-bold uppercase tracking-widest text-[#a39f98] hover:text-red-400 transition-colors mt-2 underline underline-offset-4 decoration-white/20 hover:decoration-red-400/50"
                        >
                          delete
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-y-4 gap-x-6 text-sm mb-6 border-y border-white/5 py-4">
                      <div>
                        <span className="text-[#a39f98] text-[10px] uppercase font-bold tracking-widest block mb-1">Extracted Entity</span>
                        <p className="font-medium text-white line-clamp-1">{data.name || "Undisclosed"}</p>
                      </div>
                      <div>
                        <span className="text-[#a39f98] text-[10px] uppercase font-bold tracking-widest block mb-1">Experience Level</span>
                        <p className="font-medium text-white">{data.experience_years || 0} years verified</p>
                      </div>
                      <div className="col-span-2">
                        <span className="text-[#a39f98] text-[10px] uppercase font-bold tracking-widest block mb-1">Contact Vector</span>
                        <p className="font-medium text-white">{data.email || "N/A"}</p>
                      </div>
                    </div>

                    {data.skills && data.skills.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-auto">
                        {data.skills.slice(0, 10).map((skill: string) => (
                          <span key={skill} className="px-2.5 py-1 text-[10px] uppercase font-bold tracking-widest rounded border border-white/5 text-[#a39f98] bg-[#0a0a0f]">
                            {skill}
                          </span>
                        ))}
                        {data.skills.length > 10 && (
                          <span className="px-2.5 py-1 text-[10px] uppercase font-bold tracking-widest rounded text-[#a39f98] flex items-center">
                            +{data.skills.length - 10}
                          </span>
                        )}
                      </div>
                    )}
                  </GlassCard>
                </motion.div>
              );
            })}
          </div>
        )}
      </motion.div>
    </PageContainer>
  );
}
