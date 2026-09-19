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

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        patcher = mock.patch.object(workspace_configurator, "SESSION_PATH", Path(self.directory.name) / "session.json")
        patcher.start()
        self.addCleanup(patcher.stop)

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
        broken["materializations"] = [{"template": "project-terminals", "workspace": "rns", "parameters": {}}]

        with self.assertRaises(workspace_configurator.ConfigError):
            workspace_configurator.validate_config(broken)

    def test_layout_contains_one_placeholder_per_application(self):
        workspace = self.config["templates"][0]["workspace"]
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

    @mock.patch.object(workspace_configurator, "i3")
    def test_focus_leftmost_window_uses_window_geometry(self, i3):
        i3.side_effect = [
            {
                "type": "root",
                "nodes": [
                    {
                        "type": "workspace",
                        "name": "project",
                        "nodes": [
                            {"id": 11, "window": 101, "rect": {"x": 960, "y": 0}},
                            {"id": 12, "window": 102, "rect": {"x": 0, "y": 0}},
                            {"id": 13, "window": 103, "rect": {"x": 960, "y": 540}},
                        ],
                    }
                ],
            },
            "",
        ]

        workspace_configurator.focus_leftmost_window("project", 3)

        i3.assert_called_with('[con_id=12] focus')

    @mock.patch.object(workspace_configurator.time, "sleep")
    @mock.patch.object(workspace_configurator, "i3")
    def test_wait_for_matching_windows_waits_until_window_is_mapped(self, i3, sleep):
        empty_tree = {"type": "root", "nodes": [{"type": "workspace", "name": "4", "nodes": []}]}
        mapped_tree = {
            "type": "root",
            "nodes": [
                {
                    "type": "workspace",
                    "name": "4",
                    "nodes": [
                        {
                            "window": 101,
                            "name": "Ronomepo",
                            "window_properties": {"title": "Ronomepo"},
                        }
                    ],
                }
            ],
        }
        i3.side_effect = [empty_tree, mapped_tree]

        appeared = workspace_configurator.wait_for_matching_windows("4", "title", "Ronomepo", 1)

        self.assertTrue(appeared)
        sleep.assert_called_once_with(0.05)

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

    @mock.patch.object(workspace_configurator, "i3")
    def test_session_tracks_moves_and_removes_closed_projects(self, i3):
        workspace_configurator.write_session([
            {"name": "open", "path": "/projects/open", "output": "old"},
            {"name": "closed", "path": "/projects/closed", "output": "old"},
        ])
        i3.return_value = [{"name": "open", "output": "new"}, {"name": "1", "output": "new"}]
        workspace_configurator.snapshot_session()
        self.assertEqual([{"name": "open", "path": "/projects/open", "output": "new"}],
                         workspace_configurator.read_session())

    @mock.patch.object(workspace_configurator, "setup_workspace")
    @mock.patch.object(workspace_configurator, "active_outputs", return_value=["DP-0", "HDMI-0"])
    @mock.patch.object(workspace_configurator, "i3")
    def test_restore_preserves_custom_name_folder_and_display(self, i3, outputs, setup):
        workspace_configurator.write_session([
            {"name": "custom-name", "path": self.directory.name, "output": "HDMI-0"},
        ])
        workspace_configurator.restore_projects(self.config)
        i3.assert_called_once_with('workspace "custom-name"; move workspace to output "HDMI-0"')
        workspace = setup.call_args.args[1]
        self.assertEqual("custom-name", workspace["name"])
        self.assertEqual([self.directory.name] * 3, [app["working_directory"] for app in workspace["applications"]])

    @mock.patch.object(workspace_configurator, "setup_workspace")
    @mock.patch.object(workspace_configurator, "active_outputs", return_value=["DP-0"])
    @mock.patch.object(workspace_configurator, "i3")
    def test_restore_missing_display_and_missing_directory(self, i3, outputs, setup):
        workspace_configurator.write_session([
            {"name": "missing", "path": "/missing/project-directory", "output": "HDMI-0"},
            {"name": "available", "path": self.directory.name, "output": "HDMI-0"},
        ])
        workspace_configurator.restore_projects(self.config)
        i3.assert_called_once_with('workspace "available"; move workspace to output "DP-0"')
        self.assertEqual(1, setup.call_count)

    @mock.patch.object(workspace_configurator.time, "sleep")
    @mock.patch.object(workspace_configurator, "setup_workspace")
    @mock.patch.object(workspace_configurator, "i3")
    def test_reset_resolves_session_project(self, i3, setup, sleep):
        project = {"name": "dynamic", "path": self.directory.name, "output": "HDMI-0"}
        workspace_configurator.write_session([project])
        i3.return_value = {"type": "root", "nodes": [{"type": "workspace", "name": "dynamic", "nodes": [{"id": 123}]}]}
        workspace_configurator.reset_workspace(self.config, "dynamic")
        i3.assert_any_call('[con_id=123] kill')
        self.assertEqual("dynamic", setup.call_args.args[1]["name"])
        self.assertTrue(setup.call_args.kwargs["force_layout"])
        self.assertEqual([project], workspace_configurator.read_session())

    def test_invalid_session_is_not_silently_overwritten(self):
        workspace_configurator.SESSION_PATH.write_text('{broken')
        with self.assertRaises(workspace_configurator.ConfigError):
            workspace_configurator.read_session()
        self.assertEqual('{broken', workspace_configurator.SESSION_PATH.read_text())

    @mock.patch.object(workspace_configurator, "focus_leftmost_window")
    @mock.patch.object(workspace_configurator, "wait_for_matching_windows", return_value=True)
    @mock.patch.object(workspace_configurator, "launch_app")
    @mock.patch.object(workspace_configurator.time, "sleep")
    @mock.patch.object(workspace_configurator, "i3")
    def test_reset_relaunches_after_delayed_window_close(self, i3, sleep, launch, wait, focus):
        for collection in ("nodes", "floating_nodes"):
            with self.subTest(collection=collection):
                i3.reset_mock()
                sleep.reset_mock()
                launch.reset_mock()
                closing = {"type": "workspace", "name": "4", collection: [
                    {"id": 123, "nodes": [
                        {"id": 124, "window": 101, "name": "Ronomepo"},
                    ]},
                ]}
                empty = {"type": "root", "nodes": []}
                # The old window outlives the previous fixed 0.3s delay.
                snapshots = iter([closing] * 11 + [empty, empty])

                def ipc(command=None, message_type=None):
                    return next(snapshots) if message_type == "get_tree" else []

                i3.side_effect = ipc
                workspace_configurator.reset_workspace(self.config, "4")

                i3.assert_any_call('[con_id=123] kill')
                self.assertEqual(10, sleep.call_count)
                launch.assert_called_once_with(self.config["workspaces"][1]["applications"][0])

    @mock.patch.object(workspace_configurator, "setup_workspace")
    @mock.patch.object(workspace_configurator.time, "monotonic", side_effect=[0, 31])
    @mock.patch.object(workspace_configurator, "i3")
    def test_reset_does_not_rebuild_when_window_refuses_to_close(self, i3, monotonic, setup):
        i3.return_value = {"type": "workspace", "name": "4", "nodes": [
            {"id": 123, "window": 101, "name": "Ronomepo"},
        ]}

        with self.assertRaisesRegex(workspace_configurator.ConfigError, "did not close within 30s"):
            workspace_configurator.reset_workspace(self.config, "4")

        setup.assert_not_called()

    def test_only_browser_and_ronomepo_are_fixed(self):
        self.assertEqual(["1", "4"], [item["name"] for item in self.config["workspaces"]])
        self.assertEqual([], self.config["materializations"])

    @mock.patch.object(workspace_configurator, "snapshot_session")
    @mock.patch.object(workspace_configurator, "receive_ipc")
    @mock.patch.object(workspace_configurator.select, "select", return_value=([True], [], []))
    @mock.patch.object(workspace_configurator, "i3", return_value=[{"id": 7, "name": "old"}])
    @mock.patch.object(workspace_configurator.socket, "socket")
    @mock.patch.object(workspace_configurator.subprocess, "check_output", return_value="/tmp/i3")
    def test_watcher_handles_rename_then_shutdown_without_empty_snapshot(self, command, socket, i3, select, receive, snapshot):
        workspace_configurator.write_session([{"name": "old", "path": self.directory.name, "output": "DP-0"}])
        receive.side_effect = [
            (2, {"success": True}),
            (1 << 31, {"change": "rename", "current": {"id": 7, "name": "renamed"}, "old": None}),
            ((1 << 31) + 6, {"change": "exit"}),
        ]
        self.assertFalse(workspace_configurator.watch_session_connection())
        self.assertEqual("renamed", workspace_configurator.read_session()[0]["name"])
        snapshot.assert_not_called()

    @mock.patch.object(workspace_configurator, "start_session_watcher")
    @mock.patch.object(workspace_configurator, "write_generated_i3_config")
    @mock.patch.object(workspace_configurator, "save_config")
    @mock.patch.object(workspace_configurator, "i3")
    def test_migration_records_only_open_legacy_projects(self, i3, save, generated, watcher):
        config = copy.deepcopy(self.config)
        config["materializations"] = [
            {"template": "project-terminals", "workspace": "open", "parameters": {"path": self.directory.name}},
            {"template": "project-terminals", "workspace": "closed", "parameters": {"path": self.directory.name}},
        ]
        i3.side_effect = [{"type": "root"}, [{"name": "open", "output": "HDMI-0"}]]
        workspace_configurator.enable_session(config)
        self.assertEqual([{"name": "open", "path": self.directory.name, "output": "HDMI-0"}], workspace_configurator.read_session())
        self.assertEqual([], save.call_args.args[0]["materializations"])
        watcher.assert_called_once()

    @mock.patch.object(workspace_configurator, "start_session_watcher")
    @mock.patch.object(workspace_configurator, "write_generated_i3_config")
    @mock.patch.object(workspace_configurator, "setup_workspace")
    @mock.patch.object(workspace_configurator, "restore_projects")
    @mock.patch.object(workspace_configurator, "i3")
    def test_setup_includes_restore_and_returns_to_browser(self, i3, restore, setup, generated, watcher):
        workspace_configurator.setup_all(self.config)
        self.assertEqual(["1", "4"], [call.args[1]["name"] for call in setup.call_args_list])
        restore.assert_called_once_with(self.config)
        i3.assert_called_once_with('workspace "1"')
        watcher.assert_called_once()


if __name__ == "__main__":
    unittest.main()
