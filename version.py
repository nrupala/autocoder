"""
AutoCoder Version Manager
===================
Semantic versioning for all repos with automated releases.
"""

import re
import subprocess
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class Version:
    major: int
    minor: int
    patch: int
    prerelease: str = ""
    build: str = ""
    
    def __str__(self) -> str:
        v = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            v += f"-{self.prerelease}"
        if self.build:
            v += f"+{self.build}"
        return v
    
    def __repr__(self) -> str:
        return f"Version({self.major}, {self.minor}, {self.patch}, '{self.prerelease}', '{self.build}')"
    
    def bump_major(self) -> "Version":
        return Version(self.major + 1, 0, 0)
    
    def bump_minor(self) -> "Version":
        return Version(self.major, self.minor + 1, 0)
    
    def bump_patch(self) -> "Version":
        return Version(self.major, self.minor, self.patch + 1)
    
    def to_tuple(self) -> Tuple[int, int, int]:
        return (self.major, self.minor, self.patch)
    
    @classmethod
    def parse(cls, version_str: str) -> "Version":
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.]+))?(?:\+([a-zA-Z0-9.]+))?$'
        match = re.match(pattern, version_str.strip())
        if not match:
            raise ValueError(f"Invalid version: {version_str}")
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            prerelease=match.group(4) or "",
            build=match.group(5) or ""
        )


class VersionManager:
    """
    Manages versions for all repos.
    """
    
    CHANGELOG_TEMPLATE = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [{version}] - {date}

### Changed
- Updated version system

### Fixed
- Bug fixes

"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.version_file = self.repo_path / "VERSION"
        self.changelog_file = self.repo_path / "CHANGELOG.md"
    
    def get_version(self) -> Version:
        """Get current version."""
        if self.version_file.exists():
            return Version.parse(self.version_file.read_text().strip())
        
        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            match = re.search(r'version\s*=\s*"(\d+\.\d+\.\d+)"', content)
            if match:
                return Version.parse(match.group(1))
        
        return Version(0, 1, 0)
    
    def set_version(self, version: Version, commit: bool = True):
        """Set version."""
        self.version_file.write_text(str(version))
        
        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            content = re.sub(
                r'version\s*=\s*"\d+\.\d+\.\d+"',
                f'version = "{version}"',
                content
            )
            pyproject.write_text(content)
        
        if commit:
            self.git_commit(f"Bump version to {version}")
    
    def bump(self, level: str = "patch", prerelease: str = "") -> Version:
        """Bump version."""
        current = self.get_version()
        
        if level == "major":
            new_version = current.bump_major()
        elif level == "minor":
            new_version = current.bump_minor()
        else:
            new_version = current.bump_patch()
        
        if prerelease:
            new_version.prerelease = prerelease
        
        self.set_version(new_version)
        return new_version
    
    def release(self) -> Version:
        """Create a release version."""
        current = self.get_version()
        
        if current.prerelease:
            release_version = Version(current.major, current.minor, current.patch)
            self.set_version(release_version)
            return release_version
        
        return current
    
    def git_commit(self, message: str):
        """Git commit version change."""
        try:
            subprocess.run(["git", "add", "."], cwd=self.repo_path, capture_output=True)
            subprocess.run(["git", "commit", "-m", message], cwd=self.repo_path, capture_output=True)
        except:
            pass
    
    def git_tag(self, tag: str = None):
        """Create git tag."""
        if tag is None:
            tag = f"v{self.get_version()}"
        try:
            subprocess.run(["git", "tag", tag], cwd=self.repo_path, capture_output=True)
        except:
            pass
    
    def update_changelog(self, version: Version):
        """Update changelog."""
        date = datetime.now().strftime("%Y-%m-%d")
        
        if not self.changelog_file.exists():
            self.changelog_file.write_text(self.CHANGELOG_TEMPLATE.format(version=version, date=date))
        else:
            content = self.changelog_file.read_text()
            new_entry = f"\n## [{version}] - {date}\n\n### Added\n- Initial release\n"
            content = content.replace("## [Unreleased]", new_entry + "## [Unreleased]")
            self.changelog_file.write_text(content)


class MultiRepoManager:
    """
    Manages versions across multiple repos.
    """
    
    REPOS = {
        "autocoder": "C:/Users/nrupa/autocoder",
        "uis": "D:/UIS",
        "axiomcode": "D:/axiomcode",
        "sllm": "D:/sl/projects/sllm",
    }
    
    def __init__(self):
        self.managers: Dict[str, VersionManager] = {}
        for name, path in self.REPOS.items():
            if Path(path).exists():
                self.managers[name] = VersionManager(path)
    
    def get_version(self, repo: str) -> Version:
        """Get version for a repo."""
        manager = self.managers.get(repo)
        if manager:
            return manager.get_version()
        return Version(0, 0, 0)
    
    def get_all_versions(self) -> Dict[str, str]:
        """Get all versions."""
        return {
            repo: str(manager.get_version())
            for repo, manager in self.managers.items()
        }
    
    def bump_all(self, level: str = "patch") -> Dict[str, Version]:
        """Bump all versions."""
        results = {}
        for repo, manager in self.managers.items():
            try:
                results[repo] = manager.bump(level)
            except Exception as e:
                results[repo] = None
        return results
    
    def release_all(self) -> Dict[str, Version]:
        """Release all versions."""
        results = {}
        for repo, manager in self.managers.items():
            try:
                results[repo] = manager.release()
                manager.update_changelog(results[repo])
                manager.git_commit(f"Release v{results[repo]}")
                manager.git_tag(f"v{results[repo]}")
            except Exception as e:
                results[repo] = None
        return results


# Global manager
_manager = None

def get_manager(repo: str = "autocoder") -> VersionManager:
    global _manager
    if _manager is None:
        _manager = MultiRepoManager()
    return _manager.managers.get(repo, VersionManager("C:/Users/nrupa/autocoder"))


def get_version(repo: str = "autocoder") -> str:
    return str(get_manager(repo).get_version())


def get_all_versions() -> Dict[str, str]:
    return MultiRepoManager().get_all_versions()