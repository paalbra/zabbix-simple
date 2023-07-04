#!/usr/bin/python3
import argparse
import getpass
import logging
import pyzabbix


def delete_stuff():
    global version

    if version >= (5, 4, 0):
        username_property = "username"
    else:
        username_property = "alias"

    for script in zapi.script.get():
        logging.info("Deleting script: %s (%d)", script["name"], int(script["scriptid"]))
        zapi.script.delete(script["scriptid"])

    for mediatype in zapi.mediatype.get():
        if version >= (4, 4, 0):
            logging.info("Deleting mediatype: %s (%d)", mediatype["name"], int(mediatype["mediatypeid"]))
        else:
            logging.info("Deleting mediatype: %s (%d)", mediatype["description"], int(mediatype["mediatypeid"]))
        zapi.mediatype.delete(mediatype["mediatypeid"])

    for host in zapi.host.get():
        logging.info("Deleting host: %s (%d)", host["host"], int(host["hostid"]))
        zapi.host.delete(host["hostid"])

    for template in zapi.template.get():
        logging.info("Deleting template: %s (%d)", template["host"], int(template["templateid"]))
        zapi.template.delete(template["templateid"])

    for hostgroup in zapi.hostgroup.get():
        logging.info("Deleting hostgroup: %s (%d)", hostgroup["name"], int(hostgroup["groupid"]))
        try:
            zapi.hostgroup.delete(hostgroup["groupid"])
        except pyzabbix.ZabbixAPIException as e:
            # Some hostgroups are internal and can't be deleted
            logging.error("ERROR: %s", str(e))

    if version >= (6, 2, 0):
        for templategroup in zapi.templategroup.get():
            logging.info("Deleting templategroup: %s (%d)", templategroup["name"], int(templategroup["groupid"]))
            zapi.templategroup.delete(templategroup["groupid"])

    for action in zapi.action.get():
        logging.info("Deleting action: %s (%d)", action["name"], int(action["actionid"]))
        zapi.action.delete(action["actionid"])

    for drule in zapi.drule.get():
        logging.info("Deleting drule: %s (%d)", drule["name"], int(drule["druleid"]))
        zapi.drule.delete(drule["druleid"])

    for user in zapi.user.get():
        logging.info("Deleting user: %s (%d)", user[username_property], int(user["userid"]))
        try:
            zapi.user.delete(user["userid"])
        except pyzabbix.ZabbixAPIException as e:
            # Can't delete self or internal users
            logging.error("ERROR: %s", str(e))

    for usergroup in zapi.usergroup.get():
        logging.info("Deleting usergroup: %s (%d)", usergroup["name"], int(usergroup["usrgrpid"]))
        try:
            zapi.usergroup.delete(usergroup["usrgrpid"])
        except pyzabbix.ZabbixAPIException as e:
            # Can't delete internal usergroups or only/last usergroup of user
            logging.error("ERROR: %s", str(e))


def configure_ldap():
    import ldap

    ldap_host = "localhost"
    ldap_port = 10389
    ldap_base_dn = "ou=people,dc=planetexpress,dc=com"
    ldap_search_attribute = "uid"
    ldap_bind_dn = "cn=admin,dc=planetexpress,dc=com"
    ldap_bind_password = "GoodNewsEveryone"

    if version >= (5, 4, 0):
        username_property = "username"
    else:
        username_property = "alias"

    if version >= (5, 2, 0):
        logging.info("Configuring LDAP")
        zapi.authentication.update(ldap_configured=1,
                                   ldap_host="localhost",
                                   ldap_port=ldap_port,
                                   ldap_base_dn=ldap_base_dn,
                                   ldap_search_attribute=ldap_search_attribute,
                                   ldap_bind_dn=ldap_bind_dn,
                                   ldap_case_sensitive=1,
                                   ldap_bind_password=ldap_bind_password)

        # Create read/write rights for all host groups
        hostgroup_rights = [{"permission": 3, "id": hostgroup["groupid"]} for hostgroup in zapi.hostgroup.get()]
        usergroup = zapi.usergroup.get(filter={"name": "LDAP-users"})
        if not usergroup:
            logging.info("Creating usergroup: LDAP-users")
            usergroupid = zapi.usergroup.create(name="LDAP-users", gui_access=2, rights=hostgroup_rights)["usrgrpids"][0]
        else:
            logging.info("Updating usergroup: Usergroup")
            usergroupid = usergroup[0]["usrgrpid"]
            zapi.usergroup.update(usrgrpid=usergroupid, gui_access=2, rights=hostgroup_rights)

        conn = ldap.initialize(f"ldap://{ldap_host}:{ldap_port}")
        conn.simple_bind_s(ldap_bind_dn, ldap_bind_password)
        for dn, attrs in conn.search_s("ou=people,dc=planetexpress,dc=com", ldap.SCOPE_ONELEVEL, f"{ldap_search_attribute}=*", [ldap_search_attribute]):
            username = attrs["uid"][0].decode("ascii")

            user = zapi.user.get(filter={username_property: username})

            if not user:
                logging.info("Creating user: %s", username)
                userid = zapi.user.create(roleid=2, usrgrps=[{"usrgrpid": usergroupid}], **{username_property: username})["userids"][0]
            else:
                logging.info("Updating user: %s", username)
                userid = user[0]["userid"]
                userid = zapi.user.update(userid=userid, roleid=2, usrgrps=[{"usrgrpid": usergroupid}])["userids"][0]


def create_stuff():
    global version

    logging.info("Creating hostgroup: Hostgroup")
    hostgroupid = zapi.hostgroup.create(name="Hostgroup")["groupids"][0]

    if version >= (6, 2, 0):
        logging.info("Creating templategroup: Templategroup")
        zapi.templategroup.create(name="Templategroup")["groupids"][0]

    logging.info("Creating host: Host")
    zapi.host.create(host="Host", groups=[{"groupid": hostgroupid}], interfaces=[{"type": 1, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050}])


def update_settings():
    global version

    if version >= (6, 0, 0):
        logging.info("Updating password policy")
        zapi.authentication.update(passwd_min_length=1, passwd_check_rules=0)


def update_users(current_password, new_password):
    global version

    # Create read/write rights for all host groups
    hostgroup_rights = [{"permission": 3, "id": hostgroup["groupid"]} for hostgroup in zapi.hostgroup.get()]

    usergroup = zapi.usergroup.get(filter={"name": "Usergroup"})
    if not usergroup:
        logging.info("Creating usergroup: Usergroup")
        usergroupid = zapi.usergroup.create(name="Usergroup", rights=hostgroup_rights)["usrgrpids"][0]
    else:
        logging.info("Updating usergroup: Usergroup")
        usergroupid = usergroup[0]["usrgrpid"]
        zapi.usergroup.update(usrgrpid=usergroupid, rights=hostgroup_rights)

    if version >= (5, 4, 0):
        username_property = "username"
    else:
        username_property = "alias"

    user = zapi.user.get(filter={username_property: "User"})
    if not user:
        logging.info("Creating user: User")

        if version >= (5, 2, 0):
            userid = zapi.user.create(passwd=new_password, roleid=2, usrgrps=[{"usrgrpid": usergroupid}], **{username_property: "User"})["userids"][0]
        else:
            userid = zapi.user.create(passwd=new_password, type=2, usrgrps=[{"usrgrpid": usergroupid}], **{username_property: "User"})["userids"][0]
    else:
        logging.info("Updating user: User")
        userid = user[0]["userid"]

        if version >= (5, 2, 0):
            userid = zapi.user.update(userid=userid, passwd=new_password, roleid=2, usrgrps=[{"usrgrpid": usergroupid}])["userids"][0]
        else:
            userid = zapi.user.update(userid=userid, passwd=new_password, type=2, usrgrps=[{"usrgrpid": usergroupid}])["userids"][0]

    current_username = zapi.check_authentication()[username_property]
    logging.info("Updating user: %s", current_username)
    userid = zapi.user.get(filter={username_property: current_username})[0]["userid"]

    if version >= (6, 4, 0):
        zapi.user.update(userid=userid, passwd=new_password, current_passwd=current_password)
        zapi.login(current_username, new_password)
    else:
        zapi.user.update(userid=userid, passwd=new_password)

    logging.info("Updating user: guest")


    userid = zapi.user.get(filter={username_property: "guest"})[0]["userid"]

    zapi.user.update(userid=userid, usrgrps=[{"usrgrpid": usergroupid}])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("username")
    parser.add_argument("--password")
    parser.add_argument("--new-password")
    parser.add_argument("--no-ldap", action="store_true")
    parser.add_argument("-q", "--quiet", action="store_const", default=logging.INFO, const=logging.WARNING, dest="loglevel")
    args = parser.parse_args()

    if args.password is None:
        args.password = getpass.getpass("Current password: ")
    if args.new_password is None:
        args.new_password = getpass.getpass("New password: ")

    logging.basicConfig(level=args.loglevel, format="%(levelname)s: %(message)s")

    global version

    zapi = pyzabbix.ZabbixAPI(args.url)
    zapi.login(args.username, args.password)

    version_string = zapi.api_version()
    version = tuple(map(int, version_string.split(".")))

    logging.info("Connected to Zabbix API Version %s", version_string)

    update_settings()
    delete_stuff()
    create_stuff()
    update_users(args.password, args.new_password)
    if not args.no_ldap:
        configure_ldap()
