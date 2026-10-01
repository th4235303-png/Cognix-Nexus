'use client';

import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { exportBrainVault } from '@/lib/api';

export default function ExportPage() {
  const download=async()=>{const data=await exportBrainVault();const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='cognix-brain-vault.json';a.click();URL.revokeObjectURL(url);};
  return <AppShell><PageHeader title="Unified Export" description="Export the Brain Vault as a portable, versioned JSON package." /><SectionCard title="Export"><p className="text-sm text-muted-foreground">Includes books, chapters, notes, concepts, links, and generated summaries. Secret Vault ciphertext is intentionally excluded from the knowledge export.</p><button onClick={download} className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">Download JSON export</button></SectionCard></AppShell>;
}
