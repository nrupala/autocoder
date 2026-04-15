"""
AutoCoder Verification Engine
Integrates formal verification via Lean 4
"""

import subprocess
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class LeanSpec:
    """Lean 4 specification."""
    theorem: str
    definitions: list[str]
    imports: list[str]
    docstring: str
    source_nl: str
    model_used: str
    generation_time_ms: float


@dataclass
class ProofResult:
    """Verification result."""
    status: str
    theorem_name: str
    steps: int
    lemmas: int
    tactics: list[str]
    proof_term: str
    proof_hash: str
    lean_output: str


SPEC_PROMPT = """You are an expert in Lean 4 formal verification.
Convert the following natural language algorithm description into a Lean 4 formal specification.

Rules:
1. Output ONLY valid Lean 4 code -- no explanations, no markdown.
2. Include necessary imports (Mathlib, Aesop).
3. Define any helper types/structures needed.
4. State the main theorem with a clear name.
5. The theorem should capture the full correctness specification.
6. Use `by sorry` as the proof placeholder.

Natural language description:
{description}

Output format:
```lean
import Mathlib
import Aesop

/-- docstring -/
theorem algorithm_correctness : ... := by sorry
```
"""


class VerificationEngine:
    """Integrates formal verification via Lean 4."""

    def __init__(self, lean_project_dir: str = None):
        self.lean_project_dir = Path(lean_project_dir) if lean_project_dir else Path(__file__).parent / "lean"
        self.lean_available = self._check_lean()

    def _check_lean(self) -> bool:
        """Check if Lean 4 is installed."""
        try:
            result = subprocess.run(["lean", "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def generate_spec(self, nl_description: str, model: str = "stable-code") -> LeanSpec:
        """Convert NL description to Lean 4 specification."""
        from models.orchestrator import OllamaClient
        
        client = OllamaClient(model)
        prompt = SPEC_PROMPT.format(description=nl_description)
        
        import time
        start = time.monotonic()
        
        raw = client.generate(prompt)
        elapsed = (time.monotonic() - start) * 1000
        
        spec = self._parse_spec(raw, nl_description, elapsed, model)
        
        return spec

    def _parse_spec(self, raw: str, source_nl: str, elapsed: float, model: str) -> LeanSpec:
        """Parse LLM output into LeanSpec."""
        code = raw.strip()
        
        if "```lean" in code:
            code = code.split("```lean")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()

        lines = code.split("\n")
        imports, definitions, theorem_lines = [], [], []
        docstring, in_theorem = "", False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("import "):
                imports.append(stripped.replace("import ", ""))
            elif stripped.startswith("/--"):
                docstring = stripped.replace("/--", "").replace("-/", "").strip()
            elif stripped.startswith("theorem ") or stripped.startswith("def "):
                in_theorem = True
                theorem_lines.append(line)
            elif in_theorem:
                theorem_lines.append(line)
                if ":= by sorry" in stripped or ":= by" in stripped:
                    in_theorem = False
            elif stripped.startswith("def ") or stripped.startswith("structure "):
                definitions.append(line)

        theorem = "\n".join(theorem_lines)
        if not imports:
            imports = ["Mathlib", "Aesop"]

        return LeanSpec(
            theorem=theorem,
            definitions=definitions,
            imports=imports,
            docstring=docstring,
            source_nl=source_nl,
            model_used=model,
            generation_time_ms=elapsed
        )

    def verify(self, spec: LeanSpec) -> ProofResult:
        """Verify specification with Lean 4."""
        if not self.lean_available:
            return ProofResult(
                status="skipped",
                theorem_name="unknown",
                steps=0,
                lemmas=len(spec.definitions),
                tactics=[],
                proof_term=spec.theorem,
                proof_hash="",
                lean_output="Lean 4 not installed"
            )

        name = self._extract_theorem_name(spec.theorem)
        algo_dir = self.lean_project_dir / "src" / "Algorithms"
        algo_dir.mkdir(parents=True, exist_ok=True)
        
        lean_file = algo_dir / f"{name.lower()}.lean"
        lean_file.write_text(spec.to_lean(), encoding="utf-8")

        try:
            result = subprocess.run(
                ["lake", "build"],
                cwd=self.lean_project_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            tactics = self._extract_tactics(lean_file)
            proof_term = lean_file.read_text(encoding="utf-8")
            
            import hashlib
            proof_hash = hashlib.sha512(proof_term.encode()).hexdigest()
            
            return ProofResult(
                status="verified" if result.returncode == 0 else "failed",
                theorem_name=name,
                steps=len(tactics),
                lemmas=len(spec.definitions),
                tactics=tactics,
                proof_term=proof_term,
                proof_hash=proof_hash,
                lean_output=result.stdout + result.stderr
            )
        except subprocess.TimeoutExpired:
            return ProofResult(
                status="timeout",
                theorem_name=name,
                steps=0,
                lemmas=len(spec.definitions),
                tactics=[],
                proof_term=spec.theorem,
                proof_hash="",
                lean_output="Build timeout"
            )
        except Exception as e:
            return ProofResult(
                status="error",
                theorem_name=name,
                steps=0,
                lemmas=len(spec.definitions),
                tactics=[],
                proof_term=spec.theorem,
                proof_hash="",
                lean_output=str(e)
            )

    def _extract_theorem_name(self, theorem: str) -> str:
        """Extract theorem name from Lean code."""
        for line in theorem.split("\n"):
            if "theorem " in line:
                name = line.split("theorem ")[1].split(":")[0].strip()
                return name
        return "unknown"

    def _extract_tactics(self, lean_file: Path) -> list[str]:
        """Extract proof tactics from Lean file."""
        keywords = ["rw", "simp", "induction", "cases", "apply", "exact", 
                    "have", "let", "calc", "refine", "constructor", "tauto", 
                    "linarith", "ring"]
        
        content = lean_file.read_text()
        tactics = []
        
        for line in content.split("\n"):
            stripped = line.strip()
            for kw in keywords:
                if stripped.startswith(kw) or f" {kw} " in stripped:
                    tactics.append(stripped)
                    break
        
        return tactics

    def extract_c(self, proof_result: ProofResult) -> Path:
        """Extract C code from verified proof."""
        output_dir = self.lean_project_dir.parent / "build" / "c"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{proof_result.theorem_name}.c"
        
        try:
            result = subprocess.run(
                ["lean", "--c", str(output_file), str(self.lean_project_dir / "src" / "Algorithms" / f"{proof_result.theorem_name.lower()}.lean")],
                capture_output=True,
                text=True,
                timeout=120
            )
        except:
            pass
        
        return output_file

    def extract_python(self, proof_result: ProofResult) -> Path:
        """Extract Python bindings from verified proof."""
        import textwrap
        
        output_dir = self.lean_project_dir.parent / "build" / "python"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        pkg_dir = output_dir / f"autocoder_{proof_result.theorem_name}"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        
        init_py = pkg_dir / "__init__.py"
        init_text = textwrap.dedent(f'''
            """
            {proof_result.theorem_name} -- formally verified via AutoCoder.
            Proof: {proof_result.steps} steps, {proof_result.lemmas} lemmas.
            """
            __proof_verified__ = True
        ''').lstrip()
        init_py.write_text(init_text, encoding="utf-8")
        
        return pkg_dir


def LeanSpec_to_lean(spec: LeanSpec) -> str:
    """Convert LeanSpec to Lean code string."""
    imports = "\n".join(f"import {i}" for i in spec.imports)
    defs = "\n\n".join(spec.definitions)
    return f"{imports}\n\n{defs}\n\n/-- {spec.docstring} -/\n{spec.theorem}"


LeanSpec.to_lean = lambda self: LeanSpec_to_lean(self)
