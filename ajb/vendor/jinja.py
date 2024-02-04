import os
from jinja2 import Environment, FileSystemLoader, select_autoescape, StrictUndefined


class Jinja2TemplateEngine:
    def __init__(self):
        """
        Initialize the Jinja2 environment.

        :param templates_dir: Directory where Jinja2 templates are stored.
        """
        templates_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "sendgrid/templates/"
        )
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html", "xml"]),
            undefined=StrictUndefined,  # Raise error on undefined variables
        )

    def render_template(self, template_name: str, **kwargs):
        """
        Render a template with provided data.

        :param template_name: Name of the template file.
        :param kwargs: Keyword arguments to pass to the template.
        :return: Rendered template as a string.
        """
        template = self.env.get_template(f"{template_name}/{template_name}.html")
        return template.render(**kwargs)
