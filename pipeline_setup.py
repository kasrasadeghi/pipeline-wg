# requirements:
# - notes folder in ~
# - git clone pipeline and have most recent release
# - update & upgrade
# - apt-get install git make python-is-python3

import argparse

parser = argparse.ArgumentParser(description='Setup VPN on remote host.')
parser.add_argument('--dry-run', action='store_true')
parser.add_argument('--ssh-remote', required=True)

args = parser.parse_args()


from requirement import Requirement
Requirement.configure(args.ssh_remote, args.dry_run)

# === requirements ==========================================

notes_folder = Requirement(
    desc='notes folder',
    setup='mkdir -p ~/notes',
    check='[ -d ~/notes ]',
    remote=True,
)

pipeline_packages = Requirement(
    desc='install pipeline prereqs',
    setup='apt-get update && apt-get install git make python-is-python3 -y',
    check="dpkg -l | grep git && dpkg -l | grep make && dpkg -l | grep python-is-python3",
    remote=True,
)

up_to_date = Requirement(
    desc='update & upgrade',
    setup='apt-get update && apt-get upgrade -y',
    check='false',  # always run setup
    remote=True,
)

clone_pipeline_js = Requirement(
    desc='git clone pipeline-js',
    setup='git clone https://github.com/kasrasadeghi/pipeline-js.git',
    check='[ -d pipeline-js ]',
    remote=True,
)

pipeline_systemd = Requirement(
    desc='systemd service',
    setup='cd pipeline-js && make systemd',
    check='systemctl status pipeline-notes',
    remote=True,
)