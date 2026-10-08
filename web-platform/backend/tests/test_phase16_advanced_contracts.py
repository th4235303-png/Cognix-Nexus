import unittest

from app.services.advanced_layer.contracts import GrowthMetric, OfflineHandoff, WikiEntity


class Phase16AdvancedContractTests(unittest.TestCase):
    def test_wiki_entity_keeps_source_lineage(self):
        entity = WikiEntity(
            id="entity-1",
            owner_id="owner-1",
            name="Example",
            source_refs=("chunk-1",),
        )
        self.assertEqual(entity.source_refs, ("chunk-1",))

    def test_growth_metric_is_owner_scoped(self):
        metric = GrowthMetric(
            id="metric-1",
            owner_id="owner-1",
            metric_type="consistency",
            value=0.75,
            evidence_refs=(),
        )
        self.assertEqual(metric.owner_id, "owner-1")

    def test_offline_handoff_is_explicit(self):
        handoff = OfflineHandoff(
            id="handoff-1",
            owner_id="owner-1",
            encrypted_payload_ref="capsule-1",
            signature="sig-1",
        )
        self.assertEqual(handoff.encrypted_payload_ref, "capsule-1")


if __name__ == "__main__":
    unittest.main()
