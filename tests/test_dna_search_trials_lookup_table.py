from unittest import TestCase
from dna_search_trials_lookup_table import DnaSearchTrialsLookupTable

class TestDnaSearchTrialsLookupTable(TestCase):
    def test_get_num_trials_for_finding_working_dna(self):
        dna_search_trials_lookup_table = DnaSearchTrialsLookupTable()
        self.assertEqual(dna_search_trials_lookup_table.get_num_trials_for_finding_working_dna(128), 10000)

