import copy
import importlib.machinery
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts/.local/bin/workspace-configurator"
loader = importlib.machinery.SourceFileLoader("workspace_configurator", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
workspace_configurator = importlib.util.module_from_spec(spec)
loader.exec_module(workspace_configurator)


class WorkspaceConfiguratorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_path = Path(__file__).parents[1] / "i3/.config/i3/workspaces.json"
        cls.config = json.loads(config_path.read_text(encoding="utf-8"))

    def test_shipped_configuration_is_valid(self):
        workspace_configurator.validate_config(self.config)

    def test_template_materializes_each_path_independently(self):
        config = copy.deepcopy(self.config)
        config["materializations"] = [
            {"template": "project-terminals", "workspace": "31", "parameters": {"path": "/projects/one"}},
            {"template": "project-terminals", "workspace": "32", "parameters": {"path": "/projects/two"}},
        ]
        expanded = workspace_configurator.materialize_config(config)
        workspaces = {workspace["name"]: workspace for workspace in expanded["workspaces"]}

        self.assertEqual("custom", workspaces["31"]["layout"])
        self.assertEqual(3, len(workspaces["31"]["applications"]))
        self.assertEqual("/projects/one", workspaces["31"]["applications"][0]["working_directory"])
        self.assertEqual("/projects/two", workspaces["32"]["applications"][2]["working_directory"])

    def test_missing_template_parameter_is_rejected(self):
        broken = copy.deepcopy(self.config)
        broken["materializations"][0]["parameters"] = {}

        with self.assertRaises(workspace_configurator.ConfigError):
            workspace_configurator.validate_config(broken)

    def test_layout_contains_one_placeholder_per_application(self):
        expanded = workspace_configurator.materialize_config(self.config)
        workspace = next(item for item in expanded["workspaces"] if item["name"] == "rns")
        layout = workspace_configurator.build_layout(
            workspace["layout"], workspace["applications"], workspace["layout_tree"]
        )
        placeholders = [
            node
            for node in workspace_configurator.descendants(layout)
            if node.get("swallows")
        ]

        self.assertEqual(3, len(placeholders))

    def test_common_applications_are_recognized_without_user_regexes(self):
        self.assertEqual(
            "Terminal",
            workspace_configurator.app_preset_name(workspace_configurator.APP_PRESETS["Terminal"]),
        )
        self.assertEqual(
            "Chromium",
            workspace_configurator.app_preset_name(workspace_configurator.APP_PRESETS["Chromium"]),
        )

    def test_nested_left_and_stacked_right_layout(self):
        tree = {
            "type": "split",
            "orientation": "horizontal",
            "children": [
                {"type": "app"},
                {
                    "type": "split",
                    "orientation": "vertical",
                    "children": [{"type": "app"}, {"type": "app"}],
                },
            ],
        }
        apps = [copy.deepcopy(workspace_configurator.APP_PRESETS["Terminal"]) for _ in range(3)]

        layout = workspace_configurator.build_layout("custom", apps, tree)

        self.assertEqual("splith", layout["layout"])
        self.assertEqual("splitv", layout["nodes"][1]["layout"])
        self.assertEqual(3, workspace_configurator.layout_leaf_count(tree))

    def test_relative_project_path_uses_projects_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "some-project"
            project.mkdir()

            path = workspace_configurator.resolve_project_path("some-project", root)
            workspace = workspace_configurator.project_workspace(self.config, str(project))

        self.assertEqual(project, path)
        self.assertEqual("some-project", workspace["name"])
        self.assertEqual(str(project), workspace["applications"][0]["working_directory"])
        self.assertEqual(3, len(workspace["applications"]))

    def test_absolute_project_path_is_unchanged(self):
        path = workspace_configurator.resolve_project_path("/tmp/a-project", Path("/ignored"))

        self.assertEqual(Path("/tmp/a-project"), path)

    def test_project_workspace_requires_existing_directory(self):
        with self.assertRaisesRegex(workspace_configurator.ConfigError, "does not exist"):
            workspace_configurator.project_workspace(self.config, "/missing/project-directory")

    @mock.patch.object(workspace_configurator.subprocess, "Popen")
    def test_terminal_launch_drops_dead_inherited_screen(self, popen):
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            os.environ,
            {"GNOME_TERMINAL_SCREEN": "/dead/screen", "GNOME_TERMINAL_SERVICE": ":dead"},
        ):
            app = copy.deepcopy(workspace_configurator.APP_PRESETS["Terminal"])
            app["working_directory"] = directory

            workspace_configurator.launch_app(app)

        command = popen.call_args.args[0]
        options = popen.call_args.kwargs
        self.assertEqual(["gnome-terminal", "--working-directory", directory], command)
        self.assertNotIn("GNOME_TERMINAL_SCREEN", options["env"])
        self.assertNotIn("GNOME_TERMINAL_SERVICE", options["env"])
        self.assertIsNone(options["cwd"])

    def test_save_keeps_latest_twenty_backups(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "workspaces.json"
            backup_dir = root / "backups"
            workspace_configurator.save_config(self.config, config_path, backup_dir)
            for index in range(25):
                updated = copy.deepcopy(self.config)
                updated["preferred_outputs"]["primary"] = f"output-{index}"
                workspace_configurator.save_config(updated, config_path, backup_dir)

            backups = sorted(backup_dir.glob("workspaces-*.json"))
            self.assertEqual(20, len(backups))
            newest = json.loads(backups[-1].read_text(encoding="utf-8"))
            self.assertEqual("output-23", newest["preferred_outputs"]["primary"])


if __name__ == "__main__":
    unittest.main()
