"A base16-builder written in python"
from os import path, makedirs, listdir, devnull
from shutil import rmtree
import subprocess
import click
from click_default_group import DefaultGroup
import yaml
import pystache

BASE_PATH = path.dirname(path.realpath(__file__))
SOURCES_DIR = path.join(BASE_PATH, 'sources')
SCHEMES_DIR = path.join(BASE_PATH, 'schemes')
TEMPLATES_DIR = path.join(BASE_PATH, 'templates')


@click.group(cls=DefaultGroup, default='build', default_if_no_args=True)
def cli():
    "A builder for base16 templates"


@click.command()
def update():
    "Downloads schemes"
    if not SOURCES_DIR:
        makedirs(SOURCES_DIR)
    with open(path.join(BASE_PATH, 'sources.yaml')) as source_file:
        sources = yaml.load(source_file.read())

    update_or_clone(path.join(SOURCES_DIR, 'schemes'), sources['schemes'])
    update_or_clone(path.join(SOURCES_DIR, 'templates'), sources['templates'])

    click.secho('Updating schemes...', fg='cyan')
    update_dir('schemes')

    click.secho('\nUpdating templates...', fg='cyan')
    update_dir('templates')
    click.secho('')

def update_dir(dir_name):
    "Update a directory"

    directory = path.join(BASE_PATH, dir_name)
    if not directory:
        makedirs(directory)

    with open(path.join(BASE_PATH, 'sources', dir_name, 'list.yaml')) as list_file:
        repo_list = yaml.load(list_file.read())

    count = len(repo_list.keys())
    i = 0
    for name, url in repo_list.items():
        i += 1
        click.secho('{0: <40} {1: >2}/{2}\r'.format(name,
                                                    i, count), nl=False, fg='green')
        update_or_clone(path.join(directory, name), url)

def update_or_clone(repo_path, url):
    "Updates or clones a git repository to the path repo_path"
    with open(devnull, 'w') as out:
        if path.isdir(repo_path):
            subprocess.run(['git', 'pull', url], cwd=repo_path,
                           stdout=out, stderr=subprocess.STDOUT)
        else:
            subprocess.run(['git', 'clone', url, repo_path],
                           stdout=out, stderr=subprocess.STDOUT)


@click.command()
def build():
    "Builds all the templates"
    click.secho("Building...", fg='cyan')
    if not path.isdir(TEMPLATES_DIR):
        click.secho('Run builder update first !', fg='red')
        exit(1)
    dir_count = len(listdir(TEMPLATES_DIR))
    i = 0
    for template_dir in listdir(TEMPLATES_DIR):
        i += 1
        template_name = template_dir
        template_dir = path.join(TEMPLATES_DIR, template_dir)
        if path.isdir(template_dir) and path.isdir(path.join(template_dir, 'templates')):
            click.secho('{0: <40} {1: >2}/{2}\r'.format(template_name,
                                                        i, dir_count), nl=False, fg='green')
            template_dir = path.join(template_dir, 'templates')
            with open(path.join(template_dir, 'config.yaml')) as config_file:
                config = yaml.load(config_file)
            for config_key, config in config.items():
                build_template(template_dir, config_key, config)


def build_template(template_dir, config_key, config):
    "Build a single template"
    output = path.join(template_dir, config['output'])
    if path.isdir(output):
        rmtree(output)
    makedirs(output)
    template_path = path.join(template_dir, config_key + '.mustache')
    with open(template_path) as template:
        template = template.read()
        for scheme_dir in listdir(SCHEMES_DIR):
            scheme_dir = path.join(SCHEMES_DIR, scheme_dir)
            if path.isdir(scheme_dir):
                for scheme in listdir(scheme_dir):
                    if not scheme[-5:].endswith('.yaml'):
                        continue

                    scheme_path = path.join(scheme_dir, scheme)
                    with open(scheme_path) as scheme_file:
                        scheme_yaml = yaml.load(scheme_file)

                    context = build_context(scheme_yaml, scheme)
                    output_file_path = path.join(
                        output,
                        'base16-{slug}{extension}'.format(
                            slug=context['scheme-slug'], extension=config['extension']
                        )
                    )

                    with open(output_file_path, 'w') as output_file:
                        output_file.write(pystache.render(template, context))


def build_context(scheme, filename):
    "Creates the correct template variables"
    context = {}
    rgb = 'rgb'
    for key in scheme.keys():
        if not key.startswith('base0'):
            continue
        context[key + '-hex'] = scheme[key]
        for i in range(3):
            hex_value = scheme[key][i * 2:2 * (i + 1)]
            context[key + '-hex-' + rgb[i]] = hex_value
            context[key + '-rgb-' + rgb[i]] = int(hex_value, 16)
            context[key + '-dec-' + rgb[i]] = int(hex_value, 16) / 255

    context.update({
        'scheme-name': scheme['scheme'],
        'scheme-author': scheme['author'],
        'scheme-slug': filename.lower().replace(' ', '-').replace('.yaml', '')
    })
    return context


cli.add_command(update)
cli.add_command(build)

if __name__ == '__main__':
    cli()
