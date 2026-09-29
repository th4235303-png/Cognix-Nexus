import { notFound } from 'next/navigation';
import { AppShell } from '@/components/layout/app-shell';
import { getResearchRecord } from '@/lib/researchData';
import { ResearchDetail } from '@/components/research/workspace-ui';

export default function SourceDetailPage({ params }: { params: { id: string } }) {
  const record = getResearchRecord(params.id);
  if (!record) notFound();
  return <AppShell><ResearchDetail record={record} /></AppShell>;
}
