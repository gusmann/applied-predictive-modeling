import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import field
from collections import defaultdict
import logging

from pydantic.dataclasses import dataclass
import marko

logging.basicConfig()
logger = logging.getLogger('make-chapters.py')
logger.setLevel(logging.DEBUG)
@dataclass
class Section:
    title: str
    index: int
    chapter: Optional[str] = field(default='')
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
                    title = f'{chapter} - {section_matches[1]}'.strip(),
                    index = idx,
                    chapter = 'appendix',
                    section = int(section_matches[0].split('.')[1]),
                    start_page = int(section_matches[3])
                )
            else:
                return cls(
                    title = section_matches[1].strip(),
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
        return self.title.startswith('Part ') or self.section == -1

    @property
    def is_first_section_in_chapter(self) -> bool:
        return self.section == 0 and not self.is_part

    @property
    def is_appendix(self) -> bool:
        return self.chapter == 'appendix'
    @property
    def chapter_f_name(self) -> str:
        if self.is_appendix:
            return self.chapter
        else:
            return f'chapter-{self.chapter}'

boilerplate_md = """
```{tableofcontents}
```
"""

def write_boilerplate(file_path:Path, lines:List[str], mode='w'):
    with file_path.open(mode) as f:
        f.writelines(lines)



book_sections:Dict[str,List[Section]] = defaultdict(list)
docs_path = Path('book')
table_of_contents = docs_path / 'raw_toc.txt'
with table_of_contents.open() as toc_file:
    for idx, line in enumerate(toc_file.readlines()):
        logger.debug(f"Parsing: {line}")
        section = Section.from_line(line, idx)
        logger.debug(f"Parsed: {section}")
        if section.is_first_section_in_chapter:
            # if it's a chapter's first section, ensure index file, chapter folder and sections file exist
            chapter_file = docs_path / f'{section.chapter_f_name}.md'
            if not chapter_file.exists():
                logger.debug(f"Writing boilerplate to '{chapter_file}'")
                write_boilerplate(chapter_file, [f"# {section.chapter_f_name.replace('-', ' ').capitalize()}  \n", boilerplate_md])
            chapter_folder = docs_path / section.chapter_f_name
            chapter_folder.mkdir(exist_ok=True)
            chapter_section_file = docs_path / section.chapter_f_name / f'sections.md'
            chapter_section_file.touch(exist_ok=True)
            if section.is_appendix:
                chapter_header = 'Appendix'
            else:
                chapter_header = section.title

            if chapter_header not in chapter_section_file.open().read():
                write_boilerplate(chapter_section_file, [f"# {chapter_header}  \n\n"])
        logger.debug(f"using key {section.chapter_f_name} to save {section}")
        book_sections[section.chapter_f_name].append(section)

for f_name, sections in book_sections.items():
    for section in sections:
        chapter_section_file = docs_path / f_name / f'sections.md'
        logger.info(f"checking if {f_name} '{section.title}' in {chapter_section_file}")
        if not section.is_part and not section.is_first_section_in_chapter:
            if section.title not in chapter_section_file.open().read():
                write_boilerplate(chapter_section_file, [f"## {section.title}  \n\n"], mode='a')
                # logger.info(f"{f_name} '{section.title}' not in {chapter_section_file}")
