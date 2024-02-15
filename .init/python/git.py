import os
import sys

import click


@click.command
@click.option('--repository-url', prompt='Repository URL', help='The URL of the repository to clone.')
@click.option('--folder', prompt='Folder', help='The folder to be moved as extraction from entire repository.')
@click.option('--dry-run', is_flag=True, help='Print commands without executing them.')
def git(repository_url, folder, dry_run):
    """Clone a repository.
    move a folder from entire repository to working directory
    remove the entire repository except the folder
    """
    # repository_path is working directory
    repository_path = os.getcwd() + '/' + os.path.basename(repository_url)
    # folder is path in repository
    folder = os.path.join(repository_path, folder)
    if dry_run:
        click.echo('Dry run: not executing commands.')
    click.echo('Cloning repository...')
    os.system('git clone %s' % repository_url)
    click.echo('Moving folder...')
    os.system('mv %s %s' % (folder, os.getcwd()))
    click.echo('Moved folder to %s' % os.getcwd())
    click.echo('Removing repository...')
    os.system('rm -rf %s' % os.path.basename(repository_url))
    click.echo('Done.')


if __name__ == '__main__':
    git()
