#! /usr/bin/env python3

import argparse
import glob
import logging
import os

import chevron
import yaml

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

ERROR_UNEXPECTED_TYPE = 'Object is neither a list nor a dictionary'
ERROR_MISSING_DOCKER_REQUIREMENT = 'CWL tool is missing DockerRequirement'
ERROR_MISSING_DOCKER_PULL = 'Please specify "dockerPull" in your DockerRequirement and rerun script'

def tools_list(tools_dir):
  log.debug(f'tools_dir passed to tools_list={tools_dir}')
  glob_pattern = f'{tools_dir}/*.mustache'
  log.debug(f'glob_pattern ={glob_pattern}')
  return glob.glob(glob_pattern)


# def read_tool(path):
#   with open(path) as file:
#     tool = yaml.load(file, Loader=yaml.FullLoader)
#   return tool


def parse_docker_image(tool):

  def find_docker_requirement(object):
    if type(object) is dict:
      docker_requirement = object.get('DockerRequirement', None)
      object_type = dict
    elif type(object) is list:
      docker_requirement = next((item for item in object if item['class'] == 'DockerRequirement'), None)
      object_type = list
    else:
      raise ValueError(ERROR_UNEXPECTED_TYPE)

    return docker_requirement,object_type

  docker_requirement = None

  if 'hints' in tool:
    docker_requirement, object_type = find_docker_requirement(tool['hints'])
    if docker_requirement is not None:
      parsing_metadata = {
        'docker_requirement_found_in': 'hints',
        'object_type': object_type
      }

  if docker_requirement is None and 'requirements' in tool:
    docker_requirement, object_type = find_docker_requirement(tool['requirements'])
    if docker_requirement is not None:
      parsing_metadata = {
        'docker_requirement_found_in': 'requirements',
        'object_type': object_type
      }

  if docker_requirement is None:
    raise ValueError(ERROR_MISSING_DOCKER_REQUIREMENT)

  docker_image = docker_requirement.get('dockerPull', None)

  if docker_image is None:
    raise ValueError(ERROR_MISSING_DOCKER_PULL)

  return docker_image, parsing_metadata


def edit_tool(tool, new_version):
  # docker_image, parsing_metadata = parse_docker_image(tool)
  parts = docker_image.split(':')
  parts[-1] = new_version
  tool_obj = tool[parsing_metadata['docker_requirement_found_in']]
  new_docker_image = ':'.join(parts)
  if parsing_metadata['object_type'] is dict:
    docker_requirement = tool_obj['DockerRequirement']
  else:
    docker_requirement = next((item for item in tool_obj if item['class'] == 'DockerRequirement'))
  docker_requirement['dockerPull'] = new_docker_image
  return yaml.dump(tool)


def create_tool(template_path, new_version, tools_dir):
  cwl_input = {'version': new_version}
  tool_name = os.path.basename(template_path).replace(".mustache", "")
  with open(template_path, 'r') as mus_f:
    template = chevron.render(mus_f, cwl_input)
  tool_path = os.path.join(tools_dir, tool_name)
  with open(tool_path, "w") as tool_f:
    tool_f.write(template)


def write_tool(path, output):
  with open(path, mode='w') as file:
    file.write(output)
    file.close()


def parse_args():
  parser = argparse.ArgumentParser(
    description='Change docker image version in cwl tool')
  parser.add_argument(
    'tool_dir',
    help='Dir where CWL tools are stored')
  parser.add_argument(
    'new_version',
    help='New docker version to set in cwl tool')
  parser.add_argument(
    'template_dir',
    help='Dir where CWL tool templates are stored')
  args = parser.parse_args()
  return args.tool_dir, args.new_version, args.template_dir


def main(tools_dir, new_version, template_dir):
  # tool_paths = tools_list(tools_dir)
  template_paths = tools_list(template_dir)
  for template_path in template_paths:
    #tool = read_tool(path=tool_path)
    create_tool(template_path=template_path, new_version=new_version,
                tools_dir=tools_dir)
    # output = edit_tool(tool=tool, new_version=new_version)
    # write_tool(path=tool_path, output=output)


if __name__ == '__main__':
  tools_dir, new_version, template_dir = parse_args()
  main(tools_dir=tools_dir, new_version=new_version,
       template_dir=template_dir)
