import boto3
from botocore.exceptions import ClientError

# Define variables
AWS_REGION = "us-east-1"
KEY_PAIR_NAME = 'Lenovo T410'
AMI_ID = 'ami-0c02fb55956c7d316'  # Amazon Linux 2
SUBNET_ID = 'subnet-0b939e0a4675dcbc3'
SECURITY_GROUP_ID = 'sg-01304974040835e2f'  # Ensure the Security Group allows appropriate access
INSTANCE_PROFILE = 'EC2-Admin'


# User data script
USER_DATA = '''#!/bin/bash
yum update -y
yum install python3 git -y
pip3 install boto3 requests
git clone https://github.com/levi-ochana/pokemon.git /home/ec2-user/pokemon_game
cd /home/ec2-user/pokemon_game
python3 pokemon.py
'''

# Create EC2 resource and client objects
EC2_RESOURCE = boto3.resource('ec2', region_name=AWS_REGION)
EC2_CLIENT = boto3.client('ec2', region_name=AWS_REGION)

try:
    # Create an EC2 instance
    instances = EC2_RESOURCE.create_instances(
        MinCount=1,
        MaxCount=1,
        ImageId=AMI_ID,
        InstanceType='t2.micro',
        KeyName=KEY_PAIR_NAME,
        SecurityGroupIds=[SECURITY_GROUP_ID],
        SubnetId=SUBNET_ID,
        UserData=USER_DATA,
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': 'my-ec2-instance'}]
        }]
    )

    # Wait for the instance to be running
    for instance in instances:
        print(f'EC2 instance "{instance.id}" has been launched')
        instance.wait_until_running()

        # Associate IAM Instance Profile
        EC2_CLIENT.associate_iam_instance_profile(
            IamInstanceProfile={'Name': INSTANCE_PROFILE},
            InstanceId=instance.id,
        )

        print(f'EC2 Instance Profile "{INSTANCE_PROFILE}" has been attached')
        print(f'EC2 instance "{instance.id}" is now running')

except ClientError as e:
    print(f'Error creating instance: {e}')
