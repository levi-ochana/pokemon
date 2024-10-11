import boto3
import os
import time


# Initialize EC2 resource and client
ec2 = boto3.resource('ec2')
client = boto3.client('ec2')

# Function to check if a key pair exists, if not create a new one
def check_or_create_pem(key_name="my-key-pair"):
    try:
        response = client.describe_key_pairs(KeyNames=[key_name])
        print(f"Key pair {key_name} already exists.")
        return key_name
    except client.exceptions.ClientError as e:
        if 'InvalidKeyPair.NotFound' in str(e):
            print(f"Key pair {key_name} not found, creating a new one.")
            # Create a new key pair
            key_pair = client.create_key_pair(KeyName=key_name)
            # Save the PEM file
            pem_file_path = f'~/.ssh/{key_name}.pem'
            with open(os.path.expanduser(pem_file_path), 'w') as file:
                file.write(key_pair['KeyMaterial'])
            os.chmod(os.path.expanduser(pem_file_path), 0o400)  # Set file permissions
            print(f"Key pair {key_name} created and saved to {pem_file_path}")
            return key_name
        else:
            raise e


# Function to launch an EC2 instance
def launch_instance(ami_id, key_name, security_group_id, subnet_id):
    user_data_script = '''#!/bin/bash
    sudo yum install -y python3 python3-pip git
    pip3 install requests
    git clone https://github.com/levi-ochana/pokemon.git
    '''
    
    instance = ec2.create_instances(
        ImageId=ami_id,
        InstanceType='t2.micro',
        KeyName=key_name,
        MaxCount=1,
        MinCount=1,
        SecurityGroupIds=[security_group_id],
        SubnetId=subnet_id,
        UserData=user_data_script  
    )[0]
    
    print(f"Instance {instance.id} launched.")
    instance.wait_until_running()
    instance.load()  # Refresh instance data
    
    # Wait for User Data script to complete
    while True:
        console_output = client.get_console_output(InstanceId=instance.id)
        if console_output['Output'] and ('Complete' in console_output['Output'] or 'Failed' in console_output['Output']):
            print("User Data script has completed.")
            break
        print("Waiting for User Data script to complete...")
        time.sleep(30)  # Wait for 30 seconds before checking again
    
    return instance


# Function to get a valid subnet ID from the VPC
def get_subnet_id(vpc_id):
    response = client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    if response['Subnets']:
        subnet_id = response['Subnets'][0]['SubnetId']
        print(f"Using subnet: {subnet_id} from VPC: {vpc_id}")
        return subnet_id
    else:
        raise Exception("No available subnets in the specified VPC.")

# Function to get the default VPC
def get_default_vpc():
    response = client.describe_vpcs()
    for vpc in response['Vpcs']:
        if vpc['IsDefault']:
            print(f"Using default VPC: {vpc['VpcId']}")
            return vpc['VpcId']
    raise Exception("No default VPC found.")

# Function to check or create a security group
def check_or_create_security_group(vpc_id, group_name="my-security-group"):
    try:
        response = client.describe_security_groups(GroupNames=[group_name])
        security_group_id = response['SecurityGroups'][0]['GroupId']
        print(f"Security group {group_name} already exists with ID {security_group_id}.")
        return security_group_id
    except client.exceptions.ClientError as e:
        if 'InvalidGroup.NotFound' in str(e):
            print(f"Security group {group_name} not found, creating a new one.")
            security_group = client.create_security_group(GroupName=group_name, Description='My security group', VpcId=vpc_id)
            security_group_id = security_group['GroupId']
            # Add inbound rules (allow SSH and HTTP)
            client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 80,
                        'ToPort': 80,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
            print(f"Security group {group_name} created with ID {security_group_id}.")
            return security_group_id
        else:
            raise e

# Function to get the latest Amazon Linux 2 AMI
def get_latest_ami():
    response = client.describe_images(
        Owners=['amazon'],
        Filters=[{'Name': 'name', 'Values': ['amzn2-ami-hvm-*-x86_64-gp2']}]
    )
    amis = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)
    ami_id = amis[0]['ImageId']
    print(f"Using AMI: {ami_id}")
    return ami_id

# Main workflow
def main():
    # Check or create PEM file
    key_name = check_or_create_pem()

    # Get default VPC and check/create security group
    vpc_id = get_default_vpc()
    security_group_id = check_or_create_security_group(vpc_id)

    # Get a valid subnet ID
    subnet_id = get_subnet_id(vpc_id)
    
    # Find an AMI and launch the instance
    ami_id = get_latest_ami()
    instance = launch_instance(ami_id, key_name, security_group_id, subnet_id)  
    
    
    # Ask if the user wants to connect to the instance via SSH
    connect = input("Do you want to connect to the EC2 instance? (Y/N): ").strip().upper()
    if connect == 'Y':
        os.system(f"ssh -i ~/.ssh/{key_name}.pem ec2-user@{instance.public_ip_address}")

if __name__ == '__main__':
    main()
