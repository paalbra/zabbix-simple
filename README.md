# zabbix-simple

This is meant to be a quick and simple setup of [zabbix](https://zabbix.com) v5.0 that can be used for testing purposes.

It's assumed that you run it on a Ubuntu 20.10 or CentOS 8 server.

## Prerequirements

We're going to use [podman](https://podman.io/getting-started/) and [podman-compose](https://github.com/containers/podman-compose).

### Ubuntu

```
sudo apt install -y python3-pip podman
# Depending on the package you might be missing a dependency. Install runc
sudo apt install runc
pip3 install --user podman-compose pyzabbix
```

### CentOS
```
sudo dnf install -y podman
pip3 install --user podman-compose pyzabbix
```

## Create zabbix/create pod

The `ZABBIX_PASSWORD` environment variable will be the password for the database.

The `TAG` environment variable should be set to the image tag you wish to run. E.g:

- `latest`
- `alpine-5.4-latest`
- `alpine-5.0-latest`
- `alpine-4.4-latest`
- `alpine-4.0-latest`
- `alpine-3.4-latest` (Beware that this image exposes the wrong ports. Change these manually if you really want to use this tag)
- `alpine-3.0-latest`

View available images at <https://hub.docker.com/u/zabbix>.

```
TAG=latest ZABBIX_PASSWORD=something podman-compose up -d
```

Run post-init. You may change the default password with the `--new-password` parameter.

Beware that this might hang if ran very soon after the pod starts. Wait a bit longer.

```
python3 post-init.py http://localhost:8080 Admin --password zabbix --new-password zabbix
```

## Connect

http://localhost:8080 (you could use a Nginx proxy in front of this).

There are three enabled users:

* Admin: "Zabbix Super Admin". Password is the one set with post-init.py
* User: "Zabbix Admin". Password is the one set with post-init.py
* Guest: "Zabbix User". The normal guest user without password
