import yaml


def get_config(filename='.config.yml', section='default'):
  with open(filename, 'r') as f:
    cfg = yaml.load(f)

  config = cfg['default']
  config.update(cfg[section])

  # TODO: how to handle missing keys?
  return config
