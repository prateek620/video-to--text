from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

def build(fused_knowledge: dict[str, Any], output_format: str = "markdown") -> str:
    """Build study-friendly knowledge document."""
    try:
        transcript = fused_knowledge.get("transcript", "")
        frame_insights = fused_knowledge.get("frame_insights", [])
        combined = fused_knowledge.get("combined_knowledge", "")
        
        return build_study_document(transcript, combined)
            
    except Exception as e:
        logger.exception(f"Knowledge builder error: {e}")
        raise

def build_study_document(transcript: str, combined: str) -> str:
    """Create a study-friendly document that students can use for learning."""
    
    doc = ""
    
    # Title
    doc += "# Lecture Notes\n\n"
    
    # Main content - use combined knowledge which includes transcript + visual context
    if combined and combined.strip():
        content = combined.strip()
        
        # Format the content for better readability
        # Split into logical sections
        sections = []
        current_section = []
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Start a new visual context section if we hit that marker
            if line.startswith('Visual Context from Video:'):
                if current_section:
                    sections.append('\n'.join(current_section))
                    current_section = []
                sections.append('\n## Key Visual Points\n')
            elif line.startswith('- '):
                # Bullet point for visual context
                current_section.append(line)
            else:
                current_section.append(line)
        
        # Add remaining section
        if current_section:
            sections.append('\n'.join(current_section))
        
        # Format as readable paragraphs
        for section in sections:
            if section.strip():
                # If it's already formatted (has newlines), keep it
                if '\n' in section and not section.startswith('## '):
                    # Regular content - format as paragraphs
                    sentences = []
                    current_para = []
                    
                    for line in section.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        
                        if line.startswith('- '):
                            # Bullet point
                            if current_para:
                                sentences.append('\n\n'.join(current_para))
                                current_para = []
                            sentences.append(line)
                        else:
                            current_para.append(line)
                    
                    if current_para:
                        sentences.append('\n\n'.join(current_para))
                    
                    doc += '\n\n'.join(sentences)
                else:
                    doc += section
        
        doc += "\n"
    else:
        doc += "No lecture content available.\n"
    
    return doc