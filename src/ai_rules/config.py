"""Configuration loading and management."""

from pathlib import Path
from typing import Dict, List, Optional
import yaml


class ProjectConfig:
    """Configuration for a single project."""

    def __init__(
        self, name: str, path: str, exclude_symlinks: Optional[List[str]] = None
    ):
        self.name = name
        self.path = Path(path).expanduser().resolve()
        self.exclude_symlinks = set(exclude_symlinks or [])

    def is_excluded(self, symlink_target: str) -> bool:
        """Check if a symlink target is excluded for this project."""
        normalized = Path(symlink_target).expanduser().as_posix()
        return any(
            normalized == Path(excl).expanduser().as_posix()
            for excl in self.exclude_symlinks
        )


class Config:
    """Configuration for ai-rules tool."""

    def __init__(
        self,
        exclude_symlinks: Optional[List[str]] = None,
        projects: Optional[Dict[str, ProjectConfig]] = None,
    ):
        self.exclude_symlinks = set(exclude_symlinks or [])
        self.projects = projects or {}

    @classmethod
    def load(cls, repo_root: Path) -> "Config":
        """Load configuration from available config files.

        Checks in order:
        1. ~/.ai-rules-config.yaml (user-specific) - for projects and user exclusions
        2. <repo_root>/.ai-rules-config.yaml (repo default) - for global exclusions
        3. Empty config if neither exists

        Note: Projects are only loaded from user config, not repo config.
        """
        user_config_path = Path.home() / ".ai-rules-config.yaml"
        repo_config_path = repo_root / ".ai-rules-config.yaml"

        exclude_symlinks = []
        projects = {}

        # Load user config (can contain projects and exclusions)
        if user_config_path.exists():
            with open(user_config_path, "r") as f:
                data = yaml.safe_load(f) or {}
                exclude_symlinks.extend(data.get("exclude_symlinks", []))

                # Load project configurations
                projects_data = data.get("projects", {})
                for project_name, project_data in projects_data.items():
                    if isinstance(project_data, dict):
                        project_path = project_data.get("path")
                        project_exclusions = project_data.get("exclude_symlinks", [])

                        if not project_path:
                            raise ValueError(
                                f"Project '{project_name}' is missing 'path' field"
                            )

                        projects[project_name] = ProjectConfig(
                            name=project_name,
                            path=project_path,
                            exclude_symlinks=project_exclusions,
                        )

        # Load repo config (only for global exclusions, not projects)
        if repo_config_path.exists():
            with open(repo_config_path, "r") as f:
                data = yaml.safe_load(f) or {}
                exclude_symlinks.extend(data.get("exclude_symlinks", []))

        return cls(exclude_symlinks=exclude_symlinks, projects=projects)

    def is_excluded(self, symlink_target: str) -> bool:
        """Check if a symlink target is globally excluded."""
        normalized = Path(symlink_target).expanduser().as_posix()
        return any(
            normalized == Path(excl).expanduser().as_posix()
            for excl in self.exclude_symlinks
        )

    def is_project_excluded(self, project_name: str, symlink_target: str) -> bool:
        """Check if a symlink target is excluded for a specific project.

        Combines global exclusions and project-specific exclusions.
        """
        # Check global exclusions
        if self.is_excluded(symlink_target):
            return True

        # Check project-specific exclusions
        project = self.projects.get(project_name)
        if project:
            return project.is_excluded(symlink_target)

        return False

    def validate_projects(self) -> List[str]:
        """Validate all project configurations.

        Returns list of error messages for invalid projects.
        """
        errors = []
        for project_name, project in self.projects.items():
            if not project.path.exists():
                errors.append(
                    f"Project '{project_name}' path does not exist: {project.path}"
                )
            elif not project.path.is_dir():
                errors.append(
                    f"Project '{project_name}' path is not a directory: {project.path}"
                )

        return errors
