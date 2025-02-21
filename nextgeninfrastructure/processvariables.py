import json
import os
import re
import subprocess
from typing import Dict, Tuple, List, Optional

import git
from jinja2 import Template

from nextgeninfrastructure import logger
from nextgeninfrastructure.encoder import TerraformJSONEncoder

GLOBAL_FILE = 'global-variables.tf'
EXAMPLES_FOLDER = 'examples'
SEPARATOR = '# ' + '-' * 117
NEW_LINE = '\n'


def process_examples(repo: git.Repo, repo_path: str,
                     repo_name: str, repo_version: str,
                     module_location: str,
                     write=True) -> Optional[str]:
    full_path = os.path.join(repo_path, module_location)
    examples_location = os.path.join(full_path, EXAMPLES_FOLDER)

    if not os.path.exists(examples_location) and write:
        os.mkdir(examples_location)

    config_dict = json.loads(
        exec_stdout(['terraform-config-inspect', '--json'], full_path)
    )

    sorted_variables = sorted(
        config_dict['variables'].items(),
        key=lambda x: x[1]['pos']['filename'] + str(x[1]['pos']['line'])
    )

    module_variables = [
        x for x in sorted_variables
        if x[1]['pos']['filename'] == 'variables.tf'
    ]

    common_variables = [
        x for x in module_variables
        if 'sensitive' not in x[1]['description'] and 'sensitive' not in x[1].keys()
    ]

    sensitive_variables = [
        x for x in module_variables
        if 'sensitive' in x[1]['description'] or 'sensitive' in x[1].keys()
    ]
    # existing_config = [x for x in existing_config.items() if x] if existing_config else None
    terragrunt_module_variables = '\n'.join([
        process_variable(var[0], var[1], full_path) for var in common_variables
    ])
    terraform_sensitive_module_variables = '\n'.join([
        process_variable(var[0], var[1], full_path) for var in sensitive_variables
    ]) + '\n'

    dependency_variables = [
        x for x in sorted_variables
        if x[1]['pos']['filename'] == 'variables-dependencies.tf'
    ]

    dependency_definitions = []
    dependency_inputs = []
    for var in dependency_variables:
        variable_config = process_dependency_variable(var[0], var[1], repo_path, module_location)
        dependency_definitions.append(variable_config[0])
        dependency_inputs.append(variable_config[1])

    dependency_definitions_str = f'''\
{SEPARATOR}
# Terragrunt Dependencies Management
{SEPARATOR}
''' + '\n'.join(dependency_definitions) if len(dependency_definitions) > 0 else ''

    dependency_inputs_str = f'''\
{SEPARATOR}
# TERRAGRUNT DEPENDENCIES AUTO-GENERATED. CHANGE ON YOUR OWN RISK
{SEPARATOR}
''' + '\n'.join(dependency_inputs) if len(dependency_definitions) > 0 else ''

    name_variables = f'''\
{SEPARATOR}
# Components of the name
#
# * purpose: Purpose of the resource. E.g. "upload-images"
# * separator: Name separator (defaults "-")
#
# Resource name will be <org>-<product>-<purpose>-<env>( | -<type of resource>)
#
# Example:
# * name = {{
#   purpose = "upload-images"
#   separator = "_"
# }}
{SEPARATOR}
name = {{
  purpose =
  # separator = "-"
}}

{SEPARATOR}
# Map of the custom resource tags (defaults {{}})
#
# Example:
# * tags = {{
#   Foo = "Bar"
# }}
{SEPARATOR}
# tags = {{}}\
'''

    terragrunt_file = os.path.join(module_location, 'examples', 'terragrunt.hcl')
    examples = generate_terragrunt_hcl(
        repo_name,
        repo_version,
        module_location,
        name_variables,
        terragrunt_module_variables,
        dependency_definitions_str,
        dependency_inputs_str
    )
    if write:
        with open(terragrunt_file, 'w') as f:
            f.write(examples)
        if len(sensitive_variables) > 0:
            terragrunt_keys_file = os.path.join(module_location, 'examples', 'secrets.auto.tfvars')
            with open(terragrunt_keys_file, 'w') as f:
                f.write(terraform_sensitive_module_variables)
            repo.index.add(terragrunt_keys_file)
        repo.index.add(terragrunt_file)
    else:
        return examples


def indent_string(string: str, indent: str) -> str:
    return '\n'.join([(indent + line if line != '' else '') for line in string.split('\n')]) if string != '' else None


def generate_terragrunt_hcl(
    repo_name: str,
    repo_version: str,
    module_location: str,
    name_variables: str,
    terragrunt_module_variables: str,
    terragrunt_dependency_objects_str: str,
    terragrunt_dependency_variables_str: str
) -> str:
    inputs = '\n\n'.join(
        filter(
            None,
            [
                indent_string(name_variables, '  '),
                indent_string(terragrunt_module_variables, '  '),
                indent_string(terragrunt_dependency_variables_str, '  ')
            ]
        )
    )
    return f'''\
{SEPARATOR}
# You can find latest template for this module at:
# https://github.com/{repo_name}/tree/{repo_version}/{module_location}/{EXAMPLES_FOLDER}/
{SEPARATOR}

locals {{
  stack_name    = "{module_location}"
  stack_version = "{repo_version}" # FIXME: Please update version if required

  stack_host       = "git::git@github.com"
  stack_repository = "{repo_name}"
}}

# Terragrunt will copy the Terraform configurations specified by the source
# parameter, along with any files in the working directory,
# into a temporary folder, and execute your Terraform commands in that folder.
terraform {{
  source = "${{local.stack_host}}:${{local.stack_repository}}.git//${{local.stack_name}}?ref=${{local.stack_version}}"
}}

include "root" {{
  path = find_in_parent_folders("terragrunt-core.hcl")
}}

{terragrunt_dependency_objects_str}
# TODO: These are the variables we have to pass in to use the module specified in the terragrunt configuration above:
inputs = {{
{inputs}
}}
'''


def exec_stdout(command: List[str], cwd: str) -> str:
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        cwd=cwd
    ).stdout.decode('utf-8').strip()


def process_dependency_variable(name: str, config: Dict[str, object],
                                repo_path: str,
                                module_location: str) -> Tuple[str, str]:
    if 'description' not in config:
        logger.warning(f'{module_location} variable {name} does not have description')
    description = str(config.get('description', '')).strip()

    dependency_location = os.path.join(repo_path, description)

    dependency_config = json.loads(
        exec_stdout(['terraform-config-inspect', '--json'], dependency_location)
    )['outputs']['dependency']
    dependency_object = name.replace('_dependency', '')
    if 'description' not in dependency_config:
        logger.fatal(
            f"Description was not found for {name} in {dependency_location}/{dependency_config['pos']['filename']}")

    dependency_definition = dependency_config['description']
    input_variable = f'{name} = try(dependency.{dependency_object}.outputs.dependency, {{}})'

    return dependency_definition, input_variable


def extract_literal(description: str) -> (str, Optional[str]):
    """Extracts literal values from description if present."""
    match = re.search(r"(.*)\s*<Literal>\s*(.*)</Literal>", description, re.DOTALL)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return description, None


def generate_object_defaults(variable_type: str) -> str:
    """Generates default values for object-type variables."""
    default_value_items = []
    for obj_property in variable_type.split('\n')[1:-1]:
        if not obj_property or '=' not in obj_property:
            continue
        key, value = map(str.strip, obj_property.split('=', 1))
        property_type = value.strip(')')

        if property_type.startswith('optional') and ',' in property_type:
            default_value = property_type.split(',', 1)[1].strip()
            default_value_items.append(f'# {key} = {default_value}')
        else:
            default_value_items.append(f'{key} =')

    return '{\n  ' + '\n '.join(default_value_items) + '\n}'


def process_variable(name: str, config: Dict[str, object], module_location: str) -> str:
    if 'description' not in config:
        logger.warning(f'{module_location} variable {name} does not have description')

    variable_type = str(config['type'])
    description = str(config.get('description', '')).strip()
    description, literal_value = extract_literal(description)

    is_optional = config.get('required', True) is False
    is_literal = literal_value is not None
    default_value = config.get('default')

    # Generate default values for object type variables
    default_value_str = ''
    if default_value is None and variable_type.startswith('object'):
        default_value_str = generate_object_defaults(variable_type)

    # Format default values for optional variables
    formatted_default = (
        json.dumps(
            default_value,
            sort_keys=True,
            indent=2,
            separators=(',', ' = '),
            cls=TerraformJSONEncoder
        ).replace('\n', '\n# ')
        if is_optional else default_value_str
    )

    # Jinja2 Template for rendering
    template = Template('''\
{{ separator }}
{% for line in description -%}
    {%- if line %}# {{ line }}{% else %}#{% endif %}
{% endfor -%}
{{ separator }}
{% if is_literal -%}
    {{ variable }} = {{ literal_value }}
{% elif is_optional -%}
    # {{ variable }} = {{ default_value }}
{% else -%}
    {{ variable }} = {{ default_value or '' }}
{% endif %}
''')
    return template.render(
        variable=name,
        description=description.split('\n'),
        is_optional=is_optional,
        is_literal=is_literal,
        literal_value=literal_value,
        default_value=formatted_default,
        separator=SEPARATOR
    )
