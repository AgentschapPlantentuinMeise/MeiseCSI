"""An AWS Python Pulumi program"""

import os
import pulumi
import pulumi_aws as aws
from pulumi_aws import s3

# Configuration
config = pulumi.Config()
domain_name = config.get("domain-name")
project_name = pulumi.get_project()

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

# Create and protect domain name
#Domain registration can also be handled by pulumi
#however more secure in aws console:
#https://us-east-1.console.aws.amazon.com/route53/domains/home?region=eu-west-3#/DomainSearch
#domain = aws.route53domains.Domain(
#    domain_name.replace('.','_'), name=domain_name,
#    opts=pulumi.ResourceOptions(protect=True)  # Prevents deletion
#)

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
        },
        { # flask-dev
            'protocol': 'tcp',
            'from_port': 5000,
            'to_port': 5000,
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

# Create an AWS S3 Bucket
bucket = s3.BucketV2(project_name, opts=pulumi.ResourceOptions(protect=True))
pulumi.export(f"{project_name}_bucket_name", bucket.id)

#ssh-keygen -t rsa -b 2048 -f mcsi # execute in ~/.ssh folder
#chmod g-r mcsi
#To login: ssh -i "mcsi" ec2-user@IPADRESS_SEE_EXPORT
# Read in the public key from the generated key pair file.
with open(os.path.expanduser('~/.ssh/mcsi.pub'), 'r') as key_file:
    public_key = key_file.read()
key_pair = aws.ec2.KeyPair('mcsi-key-pair', public_key=public_key)
pulumi.export('key_pair_name', key_pair.key_name)

## Secrets
badmin_secret = config.require_secret('bsKey') # Bull-Stack app init admin key
db_key_value = config.require_secret('dbKey') # Bull-Stack db connection key
jupyteradmin_secret = config.require_secret('jupyteradminSecret')
jupyterusers_secret = config.require_secret('jupyterusersSecret')

### To retrieve values in config, e.g. jupyteradminSecret: pulumi config get jupyteradminSecret

## Installation script
def create_user_data(
        badmin_secret, admin_secret, users_secret, project_name, domain_name
):
    return  f"""#!/bin/bash
#user_data script is executed as root
echo 'Executed as' $(whoami) # $USER, whoami, id -nu or logname
sudo apt update
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
sudo apt install -y docker.io docker-buildx

# Python
git clone https://github.com/AgentschapPlantentuinMeise/MeiseCSI.git
cp -r MeiseCSI/notebooks /home/ubuntu/notebooks
chmod o+w /home/ubuntu/notebooks
cd /home/ubuntu/notebooks
sudo docker run -d -p 8008:8000 -p 5050:5050 \
    -v /home/ubuntu/notebooks:/srv/jupyterhub/notebooks \
    --name jupyterhub quay.io/jupyterhub/jupyterhub jupyterhub \
    --Authenticator.allow_all=True \
    --Authenticator.admin_users='{{"admin"}}' \
    --LocalAuthenticator.create_system_users=True \
    --LocalAuthenticator.add_user_cmd='["useradd", "-m", "-p", "'$(openssl passwd -6 '{users_secret}')'"]' \
    --Spawner.default_url='/lab/tree/Welcome.ipynb' \
    --Spawner.notebook_dir='/srv/jupyterhub/notebooks'
sudo docker exec jupyterhub pip install jupyterlab jupyterlab-quarto
sudo docker exec jupyterhub pip install pandas seaborn statsmodels ipympl pingouin
# TODO get password from pulumi secret
#admin user created by jupyterhub admin_users and create_system_users combination
#sudo docker exec jupyterhub useradd -m -p $(openssl passwd -6 '{admin_secret}') admin
sudo docker exec jupyterhub apt update
# Packages to export notebooks as pdf
sudo docker exec jupyterhub apt install -y pandoc texlive
# R kernel
sudo docker exec jupyterhub apt install -y r-base
sudo docker exec jupyterhub Rscript -e 'install.packages("IRkernel"); library(IRkernel); IRkernel::installspec(user = FALSE);'
# To list: jupyter kernelspec list
# To remove: jupyter kernelspec remove ir
# Container needs to restart to find new kernels
sudo docker restart jupyterhub
sudo docker exec jupyterhub sh -c "echo 'admin:"$(openssl passwd -6 '{admin_secret}')"' | chpasswd -e"

# Nginx
sudo rm /etc/nginx/sites-enabled/default
sudo sh -c "cat - > /etc/nginx/sites-enabled/{project_name}" <<EOF
server {{
    listen 80;
    server_name www.{domain_name};
    client_max_body_size 50M;
    location / {{
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_pass http://localhost:5000;
        proxy_set_header Connection "";
        proxy_http_version 1.1;

        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }}
}}
server {{
    listen 80;
    server_name www.notebooks.{domain_name};
    client_max_body_size 50M;
    location / {{
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_pass http://localhost:8008;
        proxy_set_header Connection "";
        proxy_http_version 1.1;

        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }}
}}
server {{
    listen 80;
    server_name dev.{domain_name};
    client_max_body_size 50M;
    location / {{
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_pass http://localhost:5050;
        proxy_set_header Connection "";
        proxy_http_version 1.1;

        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }}
}}
EOF
sudo systemctl restart nginx

# Web app
sudo groupadd docker
sudo useradd -m -s /bin/bash -G docker mcsi
sudo su -l - mcsi <<"EOF"
  mkdir ~/repos && cd ~/repos
  git clone https://github.com/AgentschapPlantentuinMeise/MeiseCSI.git
  cd MeiseCSI
  docker build --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) \
    -t localhost/webapp -f rice/con/Dockerfile .
  mkdir -p ~/instance/{{batch_output,sample_output}}
  docker run -d -p 5000:5000 \
    -e BADMIN_INIT='{badmin_secret}' \
    -v ~/instance:/app/src/instance \
    --name mcsiserver localhost/webapp
EOF

# Enable ssl/https -> domain name required
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
sudo certbot -n --agree-tos --nginx --domains "www.{domain_name}" -m christophe.vanneste@plantentuinmeise.be
sudo certbot -n --agree-tos --nginx --domains "dev.{domain_name}" -m christophe.vanneste@plantentuinmeise.be
sudo certbot -n --agree-tos --nginx --domains "www.notebooks.{domain_name}" -m christophe.vanneste@plantentuinmeise.be
    
# Mail server
## hostname has to match MX record forwarding server name
sudo bash -c 'echo {domain_name} > /etc/hostname'
sudo debconf-set-selections <<< "postfix postfix/mailname string {domain_name}"
sudo debconf-set-selections <<< "postfix postfix/main_mailer_type string 'Internet Site'"
sudo apt install --assume-yes postfix
sudo apt install -y dovecot-imapd dovecot-pop3d
sudo systemctl start postfix
sudo systemctl enable postfix
sudo systemctl start dovecot
sudo systemctl enable dovecot
sudo postconf -e 'home_mailbox = Maildir/'
sudo bash -c 'echo info@{domain_name} ubuntu@{domain_name} > /etc/postfix/virtual'
# Virtual post mapping
sudo postconf -e 'virtual_alias_domains = {domain_name}'
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
#sudo postconf -e 'smtpd_tls_key_file = etc/letsencrypt/live/{domain_name}/privkey.pem'
#sudo postconf -e 'smtpd_tls_cert_file = /etc/letsencrypt/live/{domain_name}/fullchain.pem'
#sudo postconf -e 'smtpd_tls_loglevel = 1'
#sudo postconf -e 'smtpd_tls_received_header = yes'
sudo postconf -e 'myhostname = {domain_name}'
sudo systemctl restart postfix.service


# To set dovecot password for a user
#doveadm pw -s CRYPT -u user
"""

# Use apply() to resolve the secrets before passing them into user_data
user_data = pulumi.Output.all(
    badmin_secret, jupyteradmin_secret, jupyterusers_secret
).apply(
    lambda secrets: create_user_data(*secrets, project_name=project_name, domain_name=domain_name)
)

## EC2 Instance
server = aws.ec2.Instance(
    f"{domain_name.replace('.','-')}-server",
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
zone = aws.route53.get_zone(name=domain_name)
www = aws.route53.Record(
    f"{domain_name.replace('.','-')}-www",
    zone_id=zone.zone_id,
    name=f"www.{domain_name}",
    type=aws.route53.RecordType.A,
    ttl=300,
    records=[server.public_ip]
)
root_domain = aws.route53.Record(
    f"{domain_name.replace('.','-')}-root",
    zone_id=zone.zone_id,
    name=domain_name,
    type=aws.route53.RecordType.A,
    ttl=300,
    records=[server.public_ip]
)
dev_domain = aws.route53.Record(
    f"{domain_name.replace('.','-')}-dev",
    zone_id=zone.zone_id,
    name=f"dev.{domain_name}",
    type=aws.route53.RecordType.A,
    ttl=300,
    records=[server.public_ip]
)
mail_domain = aws.route53.Record(
    f"{domain_name.replace('.','-')}-mail",
    zone_id=zone.zone_id,
    name=f"mail.{domain_name}",
    type=aws.route53.RecordType.MX,
    ttl=300,
    records=["10 {domain_name}"]
)
notebooks_domain = aws.route53.Record(
    f"{domain_name.replace('.','-')}-notebooks",
    zone_id=zone.zone_id,
    name=f"www.notebooks.{domain_name}",
    type=aws.route53.RecordType.A,
    ttl=300,
    records=[server.public_ip]
)
