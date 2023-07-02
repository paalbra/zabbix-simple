# zabbix-simple

This is meant to be a quick and simple setup of [zabbix](https://zabbix.com) that can be used for testing purposes. It should at least support the specific tags/version mentioned below.

It's assumed that you run it on a Ubuntu 23.04 or Fedora 38, but can problably be used on similar distros.

## Prerequirements

We're going to use [podman](https://podman.io/getting-started/) **or** [kubernetes](https://kubernetes.io/) (kubectl).

### Podman on Ubuntu

```
sudo apt install -y podman python3-ldap python3-pip
# Depending on the package you might be missing a dependency. Install runc
sudo apt install runc
pip3 install --user pyzabbix
```

### Podman on Fedora

```
sudo dnf install -y podman python3-ldap python3-pip
pip3 install --user pyzabbix
```

### Kubernetes (kubectl)

Configuring this is out of scope for this repo. Use podman if you want a simple example.

## Create zabbix/create pod

The `ZABBIX_PASSWORD` environment variable will be the password for the database.

The `TAG` environment variable should be set to the image tag you wish to run. E.g:

- `latest`
- `alpine-6.2-latest`
- `alpine-6.0-latest`
- `alpine-5.4-latest`
- `alpine-5.0-latest`
- `alpine-4.4-latest`
- `alpine-4.0-latest`
- `alpine-3.4-latest` (Beware that this image exposes the wrong ports. Change these manually if you really want to use this tag)
- `alpine-3.0-latest`

View available images at <https://hub.docker.com/u/zabbix>.

**Podman**:
```
TAG=latest ZABBIX_PASSWORD=something envsubst < kubefile.yml | podman kube play -
```

**Kubectl**:
```
TAG=latest ZABBIX_PASSWORD=something envsubst < kubefile.yml | kubectl apply -f -
kubectl port-forward pod/zabbix-simple 8080:8080 10389:10389
```

Run post-init. You may change the default password with the `--new-password` parameter.

Beware that this might hang if ran very soon after the pod starts. Wait a bit longer.

```
python3 post-init.py http://localhost:8080 Admin --password zabbix --new-password zabbix
```

## Connect

http://localhost:8080 (you could use a Nginx proxy in front of this).

There are three enabled users by post-init:

* Admin: "Zabbix Super Admin". Password is the one set with post-init.py
* User: "Zabbix Admin". Password is the one set with post-init.py
* Guest: "Zabbix User". The normal guest user without password

LDAP is also configured and uses the users provided in the [docker-test-openldap](https://github.com/rroemhild/docker-test-openldap).
