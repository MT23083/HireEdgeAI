# resume/services/latex_parser.py
"""
LaTeX Section Parser
Extracts sections from LaTeX source for targeted editing
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class LatexSection:
    """Represents a section in the LaTeX document"""
    name: str                    # Display name (e.g., "Experience")
    section_type: str            # Type: "header", "section", "subsection"
    start_line: int              # Starting line number (1-indexed)
    end_line: int                # Ending line number (1-indexed)
    content: str                 # Raw LaTeX content of the section
    
    @property
    def line_range(self) -> str:
        """Human-readable line range"""
        return f"Lines {self.start_line}-{self.end_line}"
    
    @property
    def preview(self) -> str:
        """Short preview of content (first 100 chars)"""
        clean = self.content.replace('\n', ' ').strip()
        return clean[:100] + "..." if len(clean) > 100 else clean


def parse_latex_sections(latex_source: str) -> List[LatexSection]:
    """
    Parse LaTeX source and extract all sections.
    
    Identifies:
    - Header (content before first section)
    - \\section{...} and \\section*{...}
    - \\subsection{...} and \\subsection*{...}
    
    Args:
        latex_source: The complete LaTeX source code
        
    Returns:
        List of LatexSection objects
    """
    lines = latex_source.split('\n')
    sections: List[LatexSection] = []
    
    # Pattern to match section commands
    section_pattern = re.compile(
        r'^\\(section|subsection)\*?\{([^}]+)\}',
        re.IGNORECASE
    )
    
    # Find document body start
    doc_start = 0
    for i, line in enumerate(lines):
        if '\\begin{document}' in line:
            doc_start = i + 1
            break
    
    # Find document body end
    doc_end = len(lines)
    for i, line in enumerate(lines):
        if '\\end{document}' in line:
            doc_end = i
            break
    
    # Track section boundaries
    section_starts: List[Tuple[int, str, str]] = []  # (line_num, type, name)
    
    # Find all section starts
    for i in range(doc_start, doc_end):
        line = lines[i].strip()
        match = section_pattern.match(line)
        if match:
            section_type = match.group(1).lower()
            section_name = match.group(2)
            section_starts.append((i, section_type, section_name))
    
    # Extract header (content before first section)
    if section_starts:
        first_section_line = section_starts[0][0]
        if first_section_line > doc_start:
            header_content = '\n'.join(lines[doc_start:first_section_line])
            if header_content.strip():
                sections.append(LatexSection(
                    name="Header / Contact Info",
                    section_type="header",
                    start_line=doc_start + 1,  # 1-indexed
                    end_line=first_section_line,
                    content=header_content
                ))
    
    # Extract each section
    for idx, (start_line, section_type, section_name) in enumerate(section_starts):
        # Determine end line (start of next section or document end)
        if idx + 1 < len(section_starts):
            end_line = section_starts[idx + 1][0]
        else:
            end_line = doc_end
        
        # Extract content
        content = '\n'.join(lines[start_line:end_line])
        
        sections.append(LatexSection(
            name=section_name,
            section_type=section_type,
            start_line=start_line + 1,  # 1-indexed
            end_line=end_line,
            content=content
        ))
    
    return sections


def get_section_by_name(
    latex_source: str, 
    section_name: str
) -> Optional[LatexSection]:
    """
    Find a specific section by name.
    
    Args:
        latex_source: The complete LaTeX source
        section_name: Name to search for (case-insensitive)
        
    Returns:
        LatexSection if found, None otherwise
    """
    sections = parse_latex_sections(latex_source)
    section_name_lower = section_name.lower()
    
    for section in sections:
        if section.name.lower() == section_name_lower:
            return section
    
    return None


def replace_section_content(
    latex_source: str,
    section: LatexSection,
    new_content: str
) -> str:
    """
    Replace a section's content with new content.
    
    Args:
        latex_source: The complete LaTeX source
        section: The section to replace
        new_content: New content for the section
        
    Returns:
        Updated LaTeX source
    """
    lines = latex_source.split('\n')
    
    # Replace the section lines
    new_lines = (
        lines[:section.start_line - 1] +  # Lines before section
        new_content.split('\n') +           # New content
        lines[section.end_line:]            # Lines after section
    )
    
    return '\n'.join(new_lines)


def get_section_names(latex_source: str) -> List[str]:
    """
    Get just the names of all sections.
    
    Args:
        latex_source: The complete LaTeX source
        
    Returns:
        List of section names
    """
    sections = parse_latex_sections(latex_source)
    return [s.name for s in sections]


def get_preamble(latex_source: str) -> str:
    """
    Extract the preamble (everything before \\begin{document}).
    
    Args:
        latex_source: The complete LaTeX source
        
    Returns:
        Preamble content
    """
    lines = latex_source.split('\n')
    preamble_lines = []
    
    for line in lines:
        if '\\begin{document}' in line:
            break
        preamble_lines.append(line)
    
    return '\n'.join(preamble_lines)

