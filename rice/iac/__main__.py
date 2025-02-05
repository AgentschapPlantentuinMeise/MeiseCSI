"""An AWS Python Pulumi program"""

import os
import pulumi
import pulumi_aws as aws
from pulumi_aws import s3

# Configuration
config = pulumi.Config()

# Autotagging - https://www.pulumi.com/blog/automatically-enforcing-aws-resource-tagging-policies/
non_taggable = {'aws:route53/record:Record'} # Add resource types that should not be tagged
def register_auto_tags(auto_tags):
    pulumi.runtime.register_stack_transformation(lambda args: auto_tag(args, auto_tags))

## auto_tag applies the given tags to the resource properties if applicable.
def auto_tag(args, auto_tags):
    if args.type_ not in non_taggable:
        try: args.props['tags'] = {**(args.props['tags'] or {}), **auto_tags}
        except KeyError:
            print(args.type_, 'non taggable')
        return pulumi.ResourceTransformationResult(args.props, args.opts)

## Inject tags
register_auto_tags({
    'user:Project': pulumi.get_project(),
    'user:Stack': pulumi.get_stack(),
    'user:Cost Center': config.require('costCenter'),
})

# Create an AWS S3 Bucket
bucket = s3.BucketV2('mcsi')
pulumi.export('mcsi_bucket_name', bucket.id)

# Server
## Security
security_group = aws.ec2.SecurityGroup(
    'mcsi-secgrp',
    description='Enable HTTP access and ssh',
    ingress=[
        { # http
            'protocol': 'tcp',
            'from_port': 80,
            'to_port': 80,
            'cidr_blocks': ['0.0.0.0/0']
        },
        { # https
            'protocol': 'tcp',
            'from_port': 443,
            'to_port': 443,
            'cidr_blocks': ['0.0.0.0/0']
        },
        { # ssh
            'protocol': 'tcp',
            'from_port': 22,
            'to_port': 22,
            'cidr_blocks': ['0.0.0.0/0']
        },
        { # smtp
            'protocol': 'tcp',
            'from_port': 25,
            'to_port': 25,
            'cidr_blocks': ['0.0.0.0/0']
        },
        { # smtps submission
            'protocol': 'tcp',
            'from_port': 587,
            'to_port': 587,
            'cidr_blocks': ['0.0.0.0/0']
        },
        { # smtps
            'protocol': 'tcp',
            'from_port': 465,
            'to_port': 465,
            'cidr_blocks': ['0.0.0.0/0']
        },
        { # imap
            'protocol': 'tcp',
            'from_port': 143,
            'to_port': 143,
            'cidr_blocks': ['0.0.0.0/0']
        }
    ],
    egress=[
        { # allow all outbound traffic
            'protocol': '-1',
            'from_port': 0,
            'to_port': 0,
            'cidr_blocks': ['0.0.0.0/0'],
            'ipv6_cidr_blocks': ['::/0']
        }
    ]
)

#ssh-keygen -t rsa -b 2048 -f mcsi # execute in ~/.ssh folder
#chmod g-r mcsi
#To login: ssh -i "mcsi" ec2-user@IPADRESS_SEE_EXPORT
# Read in the public key from the generated key pair file.
with open(os.path.expanduser('~/.ssh/mcsi.pub'), 'r') as key_file:
    public_key = key_file.read()
key_pair = aws.ec2.KeyPair('mcsi-key-pair', public_key=public_key)
pulumi.export('key_pair_name', key_pair.key_name)

## Secrets
# AWS secrets to expensive will work with encrypted bucket
#db_secret = aws.secretsmanager.Secret("webdbkey", description='DB key', recovery_window_in_days=0)
db_key_value = config.require_secret('dbKey')
#db_key_secret = db_key_value.apply(
#    lambda dbKey: aws.secretsmanager.SecretVersion("db-secret-value",
#        secret_id=db_secret.id,
#        secret_string=dbKey
#    )
#)

# Export the secret ARN (useful reference for other resources)
#pulumi.export("secret_arn", db_key_secret.arn)

## Installation script
user_data = """#!/bin/bash
user_data script is executed as root
echo 'Executed as' $(whoami) # $USER, whoami, id -nu or logname
sudo apt-get update
sudo apt-get install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
sudo snap install docker
#sudo docker build -t b3app https://github.com/AgentschapPlantentuinMeise/dockshop.git#binfrastructure

# Enable ssl/https -> domain name required
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
sudo certbot -n --agree-tos --nginx --domains "www.mcsi.guardin.net" -m christophe.vanneste@plantentuinmeise.be
sudo certbot -n --agree-tos --nginx --domains "mcsi.guardin.net" -m christophe.vanneste@plantentuinmeise.be

# Web app
sudo useradd -m -s /bin/bash mcsi
sudo su -l - mcsi <<"EOF"
  mkdir ~/repos && cd ~/repos
  git clone https://github.com/AgentschapPlantentuinMeise/MeiseCSI.git
  cd MeiseCSI
  #docker build -t localhost/web .
EOF

# Mail server
## hostname has to match MX record forwarding server name
sudo bash -c 'echo mcsi.guardin.net > /etc/hostname'
sudo debconf-set-selections <<< "postfix postfix/mailname string mcsi.guardin.net"
sudo debconf-set-selections <<< "postfix postfix/main_mailer_type string 'Internet Site'"
sudo apt install --assume-yes postfix
sudo apt install -y dovecot-imapd dovecot-pop3d
sudo systemctl start postfix
sudo systemctl enable postfix
sudo systemctl start dovecot
sudo systemctl enable dovecot
sudo postconf -e 'home_mailbox = Maildir/'
sudo bash -c 'echo info@mcsi.guardin.net ubuntu@mcsi.guardin.net > /etc/postfix/virtual'
# Virtual post mapping
sudo postconf -e 'virtual_alias_domains = mcsi.guardin.net'
sudo postconf -e 'virtual_alias_maps = hash:/etc/postfix/virtual'
sudo postmap /etc/postfix/virtual
sudo postfix reload
sudo systemctl restart postfix.service
## SMTP
#sudo postconf -e 'smtpd_sasl_type = dovecot'
#sudo postconf -e 'smtpd_sasl_path = private/auth'
#sudo postconf -e 'smtpd_sasl_local_domain ='
#sudo postconf -e 'smtpd_sasl_security_options = noanonymous,noplaintext'
#sudo postconf -e 'smtpd_sasl_tls_security_options = noanonymous'
#sudo postconf -e 'broken_sasl_auth_clients = yes'
#sudo postconf -e 'smtpd_sasl_auth_enable = yes'
#sudo postconf -e 'smtpd_recipient_restrictions = \
#permit_sasl_authenticated,permit_mynetworks,reject_unauth_destination'
sudo usermod -aG mail $(whoami)
sudo apt install -y mailutils
## TLS config
sudo postconf -e 'smtp_tls_security_level = may'
sudo postconf -e 'smtpd_tls_security_level = may'
#sudo postconf -e 'smtp_tls_note_starttls_offer = yes'
#sudo postconf -e 'smtpd_tls_key_file = etc/letsencrypt/live/mcsi.guardin.net/privkey.pem'
#sudo postconf -e 'smtpd_tls_cert_file = /etc/letsencrypt/live/mcsi.guardin.net/fullchain.pem'
#sudo postconf -e 'smtpd_tls_loglevel = 1'
#sudo postconf -e 'smtpd_tls_received_header = yes'
sudo postconf -e 'myhostname = mcsi.guardin.net'
sudo systemctl restart postfix.service


# To set dovecot password for a user
#doveadm pw -s CRYPT -u user
"""

## EC2 Instance
server = aws.ec2.Instance(
    'mcsi-server',
    instance_type = 't4g.micro', # 2 vCPU 2 GiB #'t2.micro', # 1 vCPU 1 GiB mem free tier 
    ami="ami-0ae03246fb6acdee9", # for t2.micro ami-06e02ae7bdac6b938
    user_data=user_data,
    vpc_security_group_ids=[security_group.id],
    key_name=key_pair.key_name,
    root_block_device={"volume_size": 10}
)

pulumi.export('publicIp', server.public_ip)
pulumi.export('publicDns', server.public_dns)

## Domain routing
zone = aws.route53.get_zone(name="guardin.net")
www = aws.route53.Record("www.mcsi",
    zone_id=zone.zone_id,
    name="www.mcsi.guardin.net",
    type=aws.route53.RecordType.A,
    ttl=300,
    records=[server.public_ip]
)
mcsi_domain = aws.route53.Record("mcsi",
    zone_id=zone.zone_id,
    name="mcsi.guardin.net",
    type=aws.route53.RecordType.A,
    ttl=300,
    records=[server.public_ip]
)
mcsi_mail = aws.route53.Record("mcsi-mail",
    zone_id=zone.zone_id,
    name="mcsi.guardin.net",
    type=aws.route53.RecordType.MX,
    ttl=300,
    records=['10 mcsi.guardin.net']
)
