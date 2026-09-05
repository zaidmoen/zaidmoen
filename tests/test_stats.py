from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location('update_stats', Path(__file__).parents[1] / 'scripts/update_stats.py')
stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stats)
NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def repo(language='Python', stars=2, fork=False, private=False, owner='zaidmoen'):
    return {'language': language, 'stargazers_count': stars, 'fork': fork,
            'private': private, 'owner': {'login': owner}}


def snapshot(repos=()):
    return stats.summarize('zaidmoen', list(repos), 14, 13, 12,
                           [{'month': m, 'count': 0} for m in stats.month_keys(NOW)], NOW)


class StatisticsTests(unittest.TestCase):
    def test_scope_excludes_forks_private_and_other_owners(self):
        data = snapshot([repo(), repo(stars=99, fork=True), repo(stars=99, private=True), repo(stars=99, owner='other')])
        self.assertEqual(data['original_repositories'], 1)
        self.assertEqual(data['stars'], 2)

    def test_language_counts_and_missing_language(self):
        data = snapshot([repo(), repo(), repo(language='SQL'), repo(language=None)])
        self.assertEqual(data['languages'], [{'name': 'Python', 'repositories': 2}, {'name': 'SQL', 'repositories': 1}])
        self.assertEqual(data['repositories_without_language'], 1)
        self.assertIn('66.7%', stats.language_card(data))

    def test_twelve_months_cross_year_boundary(self):
        months = stats.month_keys(NOW)
        self.assertEqual(len(months), 12)
        self.assertEqual((months[0], months[-1]), ('2025-02', '2026-01'))

    def test_zero_data_and_xml_escaping(self):
        for data in [snapshot(), snapshot([repo(language='A&B <C>')])]:
            for render in [stats.overview, stats.language_card, stats.activity_card]:
                ET.fromstring(render(data))

    def test_extra_languages_are_grouped_without_losing_counts(self):
        data = snapshot([repo(language=f'Language {n}') for n in range(8)])
        svg = stats.language_card(data)
        self.assertIn('Other', svg)
        self.assertIn('3 repos · 37.5%', svg)

    def test_incomplete_search_is_an_error(self):
        with patch.object(stats, 'api', return_value={'incomplete_results': True, 'total_count': 1}):
            with self.assertRaises(RuntimeError):
                stats.search_count('author:zaidmoen type:pr')

    def test_activity_pagination_preserves_all_items(self):
        month = datetime.now(timezone.utc).strftime('%Y-%m')
        items = [{'id': n, 'created_at': month + '-01T00:00:00Z'} for n in range(101)]
        def fake(path):
            if path == '/users/zaidmoen':
                return {'followers': 14}
            if path.startswith('/users/zaidmoen/repos'):
                return []
            if 'sort=created' in path:
                return {'incomplete_results': False, 'total_count': 101,
                        'items': items[100:] if 'page=2' in path else items[:100]}
            return {'incomplete_results': False, 'total_count': 101}
        with patch.object(stats, 'api', side_effect=fake):
            result = stats.fetch_snapshot('zaidmoen')
        self.assertEqual(sum(row['count'] for row in result['monthly_pull_requests']), 101)

    def test_render_outputs_use_same_snapshot(self):
        data = snapshot([repo()])
        with tempfile.TemporaryDirectory() as folder:
            stats.render(data, Path(folder))
            self.assertEqual(len(list(Path(folder).iterdir())), 7)
            self.assertIn(data['updated_at'], (Path(folder) / 'github-overview.svg').read_text())


if __name__ == '__main__':
    unittest.main()
