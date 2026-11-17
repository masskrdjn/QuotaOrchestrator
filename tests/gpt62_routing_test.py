"""Verify that both Codex installers safely migrate the 0.10.2 routing."""

import tempfile
import tomllib
import unittest
from pathlib import Path

from terra_routing_test import PLUGIN, ROOT, load_installer


FIXTURE = ROOT / 'fixtures/release_0_10_2'
PROFILES = {
    'architect': ('gpt-6.2-astra', 'low'),
    'builder': ('gpt-6.2-sol', 'high'),
    'researcher_complex': ('gpt-6.2-sol', 'xhigh'),
    'scout_complex': ('gpt-6.2-sol', 'xhigh'),
    'strategist': ('gpt-6.2-sol', 'medium'),
}


class Gpt62Routing(unittest.TestCase):
    def test_upgrade_both_installers_and_scopes(self):
        for index, script in enumerate((ROOT / 'install.py', PLUGIN / 'scripts/install.py')):
            installer = load_installer(script, f'gpt62_installer_{index}')
            for global_scope in (False, True):
                with self.subTest(script=script, global_scope=global_scope):
                    with tempfile.TemporaryDirectory(prefix='gpt62-migration-') as temp:
                        target = Path(temp).resolve()
                        agent_dir = Path('agents' if global_scope else '.codex/agents')
                        originals = {}
                        for role in PROFILES:
                            filename = f'{role}.toml'
                            source = FIXTURE / '.codex/agents' / filename
                            originals[agent_dir / filename] = source.read_bytes()

                        skill = Path('quota-orchestrator/SKILL.md')
                        installed_skill = Path('skills' if global_scope else '.agents/skills') / skill
                        originals[installed_skill] = (FIXTURE / '.agents/skills' / skill).read_bytes()
                        for relative, content in originals.items():
                            path = target / relative
                            path.parent.mkdir(parents=True, exist_ok=True)
                            path.write_bytes(content)

                        custom = target / agent_dir / 'strategist.toml'
                        if global_scope:
                            customized = custom.read_bytes() + b'\n# local change\n'
                            custom.write_bytes(customized)
                            del originals[custom.relative_to(target)]

                        actions, _, warnings = installer.plan(target, global_scope)
                        self.assertEqual(len(warnings), int(global_scope), warnings)
                        if global_scope:
                            self.assertIn('strategist.toml', warnings[0])

                        backup = installer.apply(target, actions)
                        self.assertIsNotNone(backup)
                        for relative, content in originals.items():
                            self.assertEqual((backup / relative).read_bytes(), content)
                        for role, (model, effort) in PROFILES.items():
                            profile = target / agent_dir / f'{role}.toml'
                            if profile == custom and global_scope:
                                self.assertEqual(profile.read_bytes(), customized)
                                self.assertFalse((backup / profile.relative_to(target)).exists())
                                continue
                            config = tomllib.loads(profile.read_text(encoding='utf-8'))
                            self.assertEqual(config['model'], model)
                            self.assertEqual(config['model_reasoning_effort'], effort)

                        self.assertEqual((target / installed_skill).read_bytes(),
                                         (installer.SOURCE / '.agents/skills' / skill).read_bytes())
                        repeated, _, repeated_warnings = installer.plan(target, global_scope)
                        self.assertEqual(repeated, [])
                        self.assertEqual(repeated_warnings, warnings)
