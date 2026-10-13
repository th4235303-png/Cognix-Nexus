import { FolderOpen } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard, EmptyState } from '@/components/shared/cognix-primitives';

export default function CollectionsPage() {
  return (
    <AppShell>
      <main aria-label="Collections">
        <PageHeader
          title="Collections"
          description="Organize research into durable, named knowledge groups for downstream review and synthesis."
        />
        <SectionCard title="Your collections">
          <EmptyState
            icon={FolderOpen}
            title="No collections yet"
            description="Collection management will appear here once the collection model is enabled in the backend. Collections let you group related sources, notes, and knowledge items into reusable bundles."
          />
        </SectionCard>
      </main>
    </AppShell>
  );
}