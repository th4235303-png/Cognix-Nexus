import { Tags } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard, EmptyState } from '@/components/shared/cognix-primitives';

export default function TagsPage() {
  return (
    <AppShell>
      <main aria-label="Tags and topics">
        <PageHeader
          title="Tags &amp; Topics"
          description="Controlled vocabulary for source discovery, cross-referencing, and future search indexing across the knowledge graph."
        />
        <SectionCard title="Vocabulary">
          <EmptyState
            icon={Tags}
            title="No vocabulary configured"
            description="Tags and topics will appear here when the controlled vocabulary service is enabled. The vocabulary layer powers topic-based filtering across Sources, Knowledge Vault, and Collections."
          />
        </SectionCard>
      </main>
    </AppShell>
  );
}