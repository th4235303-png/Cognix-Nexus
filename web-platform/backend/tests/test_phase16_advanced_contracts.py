import unittest

from app.services.advanced_layer.contracts import GrowthMetric, OfflineHandoff, WikiEntity


class Phase16AdvancedContractTests(unittest.TestCase):
    def test_wiki_entity_keeps_source_lineage(self):
        entity = WikiEntity(
            id="entity-1",
            owner_id="owner-1",
            name="Example",
            entity_type="concept",
            source_refs=("chunk-1",),
        )
        self.assertEqual(entity.source_refs, ("chunk-1",))

    def test_growth_metric_is_owner_scoped(self):
        metric = GrowthMetric(
            id="metric-1",
            owner_id="owner-1",
            metric="consistency",
            value=0.75,
            unit="score",
            evidence_refs=("chunk-1",),
        )
        self.assertEqual(metric.owner_id, "owner-1")

    def test_offline_handoff_is_explicit(self):
        handoff = OfflineHandoff(
            id="handoff-1",
            owner_id="owner-1",
            format="encrypted_archive",
            artifact_ref="capsule-1",
        )
        self.assertEqual(handoff.artifact_ref, "capsule-1")
        self.assertTrue(handoff.recoverable)


if __name__ == "__main__":
    unittest.main()
