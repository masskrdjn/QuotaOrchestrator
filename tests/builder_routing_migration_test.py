"""Exercise upgrades of the 0.11.0 Codex routing instructions."""

import tempfile
import unittest
from pathlib import Path

from terra_routing_test import PLUGIN, ROOT, load_installer


FIXTURE = ROOT / 'fixtures/release_0_11_0'
SKILL = Path('.agents/skills/quota-orchestrator/SKILL.md')


class BuilderRoutingMigration(unittest.TestCase):
    def test_migrates_managed_instructions_and_preserves_project_notes(self):
        for index, script in enumerate((ROOT / 'install.py', PLUGIN / 'scripts/install.py')):
            installer = load_installer(script, f'builder_routing_installer_{index}')
            for global_scope in (False, True):
                with self.subTest(script=script, global_scope=global_scope):
                    with tempfile.TemporaryDirectory(prefix='builder-routing-') as temp:
                        target = Path(temp).resolve()
                        installed_skill = Path('skills/quota-orchestrator/SKILL.md') if global_scope else SKILL
                        notes = b'# Local instructions\r\n\r\n'
                        before = self.managed_agents(installer, notes, FIXTURE)
                        originals = {
                            Path('AGENTS.md'): before,
                            installed_skill: (FIXTURE / SKILL).read_bytes(),
                        }
                        for relative, content in originals.items():
                            path = target / relative
                            path.parent.mkdir(parents=True, exist_ok=True)
                            path.write_bytes(content)

                        actions, _, warnings = installer.plan(target, global_scope)
                        self.assertEqual(warnings, [])
                        backup = installer.apply(target, actions)
                        self.assertIsNotNone(backup)
                        for relative, content in originals.items():
                            self.assertEqual((backup / relative).read_bytes(), content)
                        after = self.managed_agents(installer, notes, installer.SOURCE)
                        self.assertEqual((target / 'AGENTS.md').read_bytes(), after)
                        self.assertEqual((target / installed_skill).read_bytes(),
                                         (installer.SOURCE / SKILL).read_bytes())
                        repeated, _, warnings = installer.plan(target, global_scope)
                        self.assertEqual(repeated, [])
                        self.assertEqual(warnings, [])

                        customized = after.replace(b'## Triage', b'## Custom triage')
                        (target / 'AGENTS.md').write_bytes(customized)
                        actions, _, warnings = installer.plan(target, global_scope)
                        self.assertEqual(actions, [])
                        self.assertEqual(len(warnings), 1)
                        self.assertIn('bloc codexskills existant conserv', warnings[0])

    @staticmethod
    def managed_agents(installer, notes, source):
        block = (source / 'AGENTS.md').read_bytes().replace(b'\r\n', b'\n')
        return (notes + installer.START.encode() + b'\r\n'
                + block.rstrip(b'\n').replace(b'\n', b'\r\n') + b'\r\n'
                + installer.END.encode() + b'\r\n')
