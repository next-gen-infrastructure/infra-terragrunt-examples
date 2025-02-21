import json

from typing import Any


class TerraformJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        # Get the indent and separators from kwargs, or set defaults if not provided
        self.indent = kwargs.get('indent', 2)
        self.sep_comma, self.sep_colon = ('', ' = ')
        super().__init__(*args, **kwargs)

    def encode(self, obj: Any) -> str:
        # If the object is a dictionary, process it without quotes on keys
        if isinstance(obj, dict):
            items = []
            if len(obj.keys()) == 0:
                return "{}"
            for key, value in obj.items():
                original_indent = self.indent
                self.indent += self.indent
                encoded_value = self.encode(value)  # Recursively encode the value
                self.indent = original_indent
                items.append(f"{key}{self.sep_colon}{encoded_value}")  # Custom separators
            if self.indent is not None:  # Apply indentation if required
                indent_space = ' ' * self.indent
                indent_end = ' ' * (self.indent // 2)
                return ("{\n" +
                        f"{self.sep_comma}\n".join(
                            [f"{indent_space}{item}" for item in items]
                        ) +
                        f"\n{indent_end}}}"
                        )
            else:
                return "{" + f"{self.sep_comma}".join(items) + "}"
        # For other types, use the default encoder (which adds quotes if needed)
        return super().encode(obj)
