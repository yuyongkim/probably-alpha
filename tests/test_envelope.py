"""Tests for sepa.contracts.envelope."""
from sepa.contracts.envelope import reset_run_id, wrap_output


class TestEnvelope:
    def test_wrap_list(self):
        result = wrap_output([1, 2, 3], date_dir='20260403')
        assert result['schema_version'] == '1.0'
        assert result['date'] == '20260403'
        assert result['stale_data'] is False
        assert result['items'] == [1, 2, 3]
        assert 'generated_at' in result
        assert 'pipeline_run_id' in result

    def test_wrap_dict(self):
        result = wrap_output({'key': 'value'}, date_dir='20260403')
        assert result['key'] == 'value'
        assert result['schema_version'] == '1.0'

    def test_stale_flag(self):
        result = wrap_output([], stale_data=True)
        assert result['stale_data'] is True

    def test_run_id_consistent(self):
        reset_run_id()
        r1 = wrap_output([])
        r2 = wrap_output([])
        assert r1['pipeline_run_id'] == r2['pipeline_run_id']

    def test_run_id_resets(self):
        reset_run_id()
        r1 = wrap_output([])
        reset_run_id()
        r2 = wrap_output([])
        assert r1['pipeline_run_id'] != r2['pipeline_run_id']
