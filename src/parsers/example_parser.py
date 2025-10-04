"""
Example parser implementation demonstrating how to use BaseParser.
"""

from .base_parser import BaseParser


class ExampleParser(BaseParser):
    """
    Example parser that converts text files to markdown.

    Usage:
        parser = ExampleParser("Important NPCs.txt", output_dir="docs/npcs")
        markdown_path, data_path = parser.run(save_data=True)
    """

    def __init__(
        self, input_file: str, output_dir: str = "docs", parsed_data_dir: str = "parsed"
    ):
        """
        Initialize the example parser.

        Args:
            input_file: Input file in data/documentation/
            output_dir: Output directory for markdown (can include subdirectory like "docs/npcs")
            parsed_data_dir: Subdirectory in data/documentation/parsed/ for data files
        """
        super().__init__(input_file, output_dir, parsed_data_dir)

    def parse(self) -> dict:
        """
        Parse the input text file.

        Returns:
            dict: Parsed content with sections
        """
        content = self.input_path.read_text(encoding="utf-8")

        # Example: split by double newlines to get sections
        sections = content.split("\n\n")

        return {
            "title": self.input_path.stem,
            "sections": sections,
            "line_count": len(content.splitlines()),
        }

    def generate_markdown(self, parsed_data: dict) -> str:
        """
        Generate markdown from parsed data.

        Args:
            parsed_data: Data from parse()

        Returns:
            str: Markdown content
        """
        lines = [
            f"# {parsed_data['title']}\n",
            f"*Source: {self.input_path.name}*\n",
            f"*Lines: {parsed_data['line_count']}*\n",
            "---\n",
        ]

        for i, section in enumerate(parsed_data["sections"], 1):
            if section.strip():
                lines.append(f"\n## Section {i}\n")
                lines.append(f"{section}\n")

        return "\n".join(lines)


# Example usage (for reference)
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    # Example 1: Simple parsing to docs/
    parser = ExampleParser("Important NPCs.txt")
    markdown_path, _ = parser.run()
    print(f"Markdown saved to: {markdown_path}")

    # Example 2: Parse to subdirectory and save data
    parser = ExampleParser(
        "Important NPCs.txt", output_dir="docs/npcs", parsed_data_dir="npcs"
    )
    markdown_path, data_path = parser.run(save_data=True)
    print(f"Markdown: {markdown_path}")
    print(f"Data: {data_path}")
