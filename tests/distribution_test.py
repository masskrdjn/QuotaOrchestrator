"""Keep version references and independently installed distribution copies aligned."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugins/quota-orchestrator'
TEMPLATES = PLUGIN / 'templates'


class Distribution(unittest.TestCase):
    def test_both_hosts_resolve_the_same_package(self):
        codex_catalog = json.loads((ROOT / '.agents/plugins/marketplace.json').read_text(encoding='utf-8'))
        claude_catalog = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text(encoding='utf-8'))
        codex_entry, = codex_catalog['plugins']
        claude_entry, = claude_catalog['plugins']
        self.assertEqual((ROOT / codex_entry['source']['path']).resolve(), PLUGIN)
        self.assertEqual((ROOT / claude_entry['source']).resolve(), PLUGIN)
        codex = json.loads((PLUGIN / '.codex-plugin/plugin.json').read_text(encoding='utf-8'))
        claude = json.loads((PLUGIN / '.claude-plugin/plugin.json').read_text(encoding='utf-8'))
        self.assertEqual(codex['name'], codex_entry['name'])
        self.assertEqual(claude['name'], claude_entry['name'])
        self.assertEqual(codex['version'], claude['version'])

        for path in ('skills', 'hooks/hooks.json', 'CLAUDE.md', 'AGENTS.md'):
            self.assertFalse((PLUGIN / path).exists(), f'Implicitly loaded component: {path}')
        codex_skills = (PLUGIN / codex['skills']).glob('*/SKILL.md')
        claude_skills = (PLUGIN / claude['skills']).glob('*/SKILL.md')
        self.assertEqual({p.parent.name for p in codex_skills},
                         {'quota-orchestrator', 'quota-orchestrator-setup'})
        self.assertEqual({p.parent.name for p in claude_skills}, {'quota-orchestrator'})
        codex_hooks = json.loads((PLUGIN / codex['hooks']).read_text(encoding='utf-8'))['hooks']
        self.assertEqual(set(codex_hooks), {'SessionStart', 'PreToolUse'})
        self.assertEqual(set(claude['hooks']), {'SessionStart', 'PostToolUse'})

    def test_current_version_matches_readmes_and_changelog(self):
        version = json.loads((PLUGIN / '.codex-plugin/plugin.json').read_text(encoding='utf-8'))['version']
        self.assertRegex(version, r'^\d+\.\d+\.\d+$')
        for filename, label in (('README.md', 'Current plugin version'),
                                ('README.fr.md', 'Version actuelle du plugin')):
            text = (ROOT / filename).read_text(encoding='utf-8')
            match = re.search(re.escape(label) + r'\s*:\s*\*\*([^*]+)\*\*', text)
            self.assertIsNotNone(match, filename)
            self.assertEqual(match[1], version, filename)
        entries = re.findall(r'^## (\d+\.\d+\.\d+) — \d{4}-\d{2}-\d{2}',
                             (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8'), re.MULTILINE)
        self.assertTrue(entries, 'Missing dated changelog entry')
        self.assertEqual(entries[0], version)
        self.assertEqual(len(entries), len(set(entries)), 'Duplicate changelog version')

    def test_installed_sources_match_repository_sources(self):
        expected = {Path('AGENTS.md'), Path('.codex/config.toml'),
                    Path('.agents/skills/quota-orchestrator/SKILL.md')}
        expected.update(path.relative_to(ROOT) for path in (ROOT / '.codex/agents').glob('*.toml'))
        actual = {path.relative_to(TEMPLATES) for path in TEMPLATES.rglob('*') if path.is_file()}
        self.assertEqual(actual, expected)
        for relative in sorted(expected):
            with self.subTest(path=relative):
                self.assertEqual((ROOT / relative).read_bytes(), (TEMPLATES / relative).read_bytes())

    def test_installers_differ_only_in_source_location(self):
        repository = (ROOT / 'install.py').read_text(encoding='utf-8')
        bundled = (PLUGIN / 'scripts/install.py').read_text(encoding='utf-8')
        source = 'SOURCE = Path(__file__).resolve().parent\n'
        self.assertEqual(repository.count(source), 1)
        self.assertEqual(repository.replace(source,
                         'SOURCE = Path(__file__).resolve().parent.parent / "templates"\n', 1), bundled)


if __name__ == '__main__':
    unittest.main()
