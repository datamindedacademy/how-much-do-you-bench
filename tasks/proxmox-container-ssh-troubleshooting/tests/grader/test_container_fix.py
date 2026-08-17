"""Hidden grader for exercise 19 (reverse-proxy container: no SSH).

The bug is the container's OS image: `template_file_id` points at an **OCI**
application image. OCI images are Docker-style single-process root filesystems
with no init system and no `openssh-server`, so nothing runs sshd -- Terraform's
SSH provisioner (and a manual `ssh`) can never connect. The fix is to use a
*standard* Proxmox LXC **system** template (systemd + openssh-server), which is
what LXC containers are meant to boot from. This grader reads the Terraform the
model shipped and checks the container no longer boots an OCI image and now uses
a standard LXC template, while the SSH wiring stays intact.
"""
import re

import hcl_lite
import pytest


@pytest.fixture(scope="session")
def container(tf_text):
    cts = hcl_lite.resources(tf_text, "proxmox_virtual_environment_container")
    assert cts, "the proxmox_virtual_environment_container must stay in place"
    return cts[0]


def _template_ids(tf_text):
    # Every string literal assigned to template_file_id anywhere in the config.
    return re.findall(r'template_file_id\s*=\s*"([^"]+)"', tf_text)


def test_ssh_wiring_intact(container, tf_text):
    # The whole point is to keep SSH working, so the key + provisioner must stay.
    assert "user_account" in container.body, \
        "the container must keep its user_account { keys = ... } so the SSH key is installed"
    assert "ssh_public_keys" in container.body, "the SSH public keys must stay wired to the container"
    assert re.search(r'provisioner\s+"remote-exec"', tf_text), \
        "the SSH remote-exec provisioner (install_caddy) must stay -- the container is provisioned over SSH"


def test_not_an_oci_image(tf_text):
    ids = _template_ids(tf_text)
    assert ids, "could not find a template_file_id on the container"
    for tid in ids:
        assert "oci" not in tid.lower(), (
            f"template_file_id={tid!r} is an OCI image: no init/sshd, so SSH can never work; "
            "use a standard LXC system template instead"
        )


def test_standard_lxc_template(tf_text):
    ids = _template_ids(tf_text)
    assert ids, "could not find a template_file_id on the container"
    # A real Proxmox LXC template lives in the vztmpl store and, for the shipped
    # system images, carries the word "standard" (e.g. debian-13-standard_...).
    assert any("vztmpl" in tid and "standard" in tid.lower() for tid in ids), (
        "point template_file_id at a standard LXC system template "
        "(e.g. local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst)"
    )
