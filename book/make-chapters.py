import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import field
from collections import defaultdict
import logging

from pydantic.dataclasses import dataclass

logger = logging.getLogger("make-chapters.py")

@dataclass
class Section:
    title: str
    index: int
    chapter: Optional[str] 
    section: Optional[int] = field(default=-1)
    start_page: Optional[int] = field(default=-1)
    
    @classmethod
    def from_line(cls, line:str, idx: int):
        matches = re.findall('(^\S+\.\d+?) (.*?)(\.+)(\d+)', line)
        if matches:
            section_matches = matches[0]
            chapter = section_matches[0].split('.')[0]
            if not chapter.isnumeric():
                return cls(
                    title = section_matches[1],
                    index = idx,
                    chapter = 'appendix',
                    section = int(section_matches[0].split('.')[1]),
                    start_page = int(section_matches[3])
                )
            else:
                return cls(
                    title = section_matches[1],
                    index = idx,
                    chapter = chapter,
                    section = int(section_matches[0].split('.')[1]),
                    start_page = int(section_matches[3])
                )
        else:
            # this is a part section
            return cls(
                title = line.strip(),
                index = idx
            )

    @property
    def is_part(self) -> bool:
        return self.title.startswith('Part ') and self.section == -1

    @property
    def is_first_section_in_chapter(self) -> bool:
        return self.section == 0 and not self.is_part
    @property
    def is_appendix(self) -> bool:
        return self.chapter == 'appendix'

    @property
    def chapter_f_name(self) -> str:
        if self.is_appendix:
            return 'appendix'
        else:
            return f'chapter-{self.chapter}'

boilerplate_md = """
```{tableofcontents}
```

"""

def write_boilerplate(file_path:Path, lines:List[str]):
    with file_path.open('w') as f:
        f.writelines(lines)

book_sections:List[Section] = []
docs_path = Path('.')
table_of_contents = docs_path / 'raw_toc.txt'
with table_of_contents.open() as toc_file:
    for idx, line in enumerate(toc_file.readlines()):
        section = Section.from_line(line, idx)
        if section.is_first_section_in_chapter:
            # if it's a chapter's first section, ensure index file, chapter folder and sections file exist
            chapter_file = docs_path / f'{section.chapter_f_name}.md'
            if not chapter_file.exists():
                logger.info(f"Writing boilerplate to '{chapter_file}'")
                write_boilerplate(chapter_file, [f"# {section.title}", boilerplate_md])
            chapter_folder = docs_path / section.chapter_f_name
            chapter_folder.mkdir(exist_ok=True)
        book_sections.append(section)

for section in book_sections:
    chapter_section_file = docs_path / section.chapter_f_name / f'sections.md'

