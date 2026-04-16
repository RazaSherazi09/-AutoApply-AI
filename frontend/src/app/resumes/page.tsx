"use client";

import { useEffect, useState } from "react";
import { resumesApi, type Resume } from "@/lib/api";
import { motion } from "framer-motion";
import { FileText, CheckCircle2 } from "lucide-react";
import PageContainer from "@/components/PageContainer";
import UploadDropzone from "@/components/UploadDropzone";

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
      setUploadResult(`✅ Document v${result.version} analyzed.`);
      await loadResumes();
    } catch (err: unknown) {
      setUploadResult(`❌ ${err instanceof Error ? err.message : "Upload failed"}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this resume? This cannot be undone.")) return;
    
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
          Resumes
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          className="text-[var(--muted-fg)] text-lg"
        >
          Documents are parsed into matching vectors.
        </motion.p>
      </header>

      <UploadDropzone 
        onUpload={handleUpload}
        uploading={uploading}
        uploadResult={uploadResult}
      />

      {/* Existing Resumes */}
      <motion.div 
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
      >
        <div className="flex items-center justify-between border-b border-[var(--border)] pb-4 mb-8">
          <h2 className="text-xl md:text-2xl font-bold tracking-tight text-[var(--foreground)]" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.04em' }}>
            Archive
          </h2>
          <span className="label-upper">{total} Files</span>
        </div>

        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[var(--accent)]" />
          </div>
        ) : resumes.length === 0 ? (
          <div className="text-center py-20 border border-[var(--border)]">
            <p className="text-2xl font-bold text-[var(--foreground)] tracking-tight mb-2" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.04em' }}>Empty.</p>
            <p className="text-sm text-[var(--muted-fg)] font-mono uppercase tracking-wider">Upload a PDF to begin</p>
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
                  <div className="border border-[var(--border)] hover:border-[var(--border-hover)] transition-[border-color] duration-150 p-6 md:p-8 flex flex-col h-full relative group">
                    {/* Accent bar */}
                    <div className="absolute top-0 left-0 h-[2px] w-12 bg-[var(--accent)]" />

                    <div className="flex items-start justify-between mb-6">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 border border-[var(--border)] flex items-center justify-center text-[var(--muted-fg)] group-hover:text-[var(--accent)] group-hover:border-[var(--accent)] transition-colors">
                          <FileText size={18} strokeWidth={1.5} />
                        </div>
                        <div>
                          <h4 className="font-bold text-lg text-[var(--foreground)] group-hover:text-[var(--accent)] transition-colors line-clamp-1 tracking-tight" style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.04em' }}>{r.file_name}</h4>
                          <p className="label-upper mt-1">Version {r.version} — {new Date(r.created_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <span className="badge badge-primary flex items-center gap-1.5">
                          <CheckCircle2 size={10} strokeWidth={1.5} /> Active
                        </span>
                        <button 
                          onClick={() => handleDelete(r.id)}
                          className="label-upper text-[var(--muted-fg)] hover:text-[var(--error)] transition-colors underline underline-offset-4 decoration-[var(--border)] hover:decoration-[var(--error)]"
                        >
                          delete
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-y-4 gap-x-6 text-sm mb-6 border-y border-[var(--border)] py-4">
                      <div>
                        <span className="label-upper block mb-1">Name</span>
                        <p className="font-medium text-[var(--foreground)] line-clamp-1">{data.name || "—"}</p>
                      </div>
                      <div>
                        <span className="label-upper block mb-1">Experience</span>
                        <p className="font-medium text-[var(--foreground)]">{data.experience_years || 0} years</p>
                      </div>
                      <div className="col-span-2">
                        <span className="label-upper block mb-1">Contact</span>
                        <p className="font-medium text-[var(--foreground)]">{data.email || "N/A"}</p>
                      </div>
                    </div>

                    {data.skills && data.skills.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-auto">
                        {data.skills.slice(0, 10).map((skill: string) => (
                          <span key={skill} className="badge badge-neutral">
                            {skill}
                          </span>
                        ))}
                        {data.skills.length > 10 && (
                          <span className="label-upper self-center">
                            +{data.skills.length - 10}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </motion.div>
    </PageContainer>
  );
}
