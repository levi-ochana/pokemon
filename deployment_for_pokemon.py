import os
import subprocess
import json

# Function to check if the key file exists and is readable
def check_key_file(key_file):
    if not os.path.exists(key_file):
        print(f"Key file does not exist: {key_file}")
        return False
    if not os.access(key_file, os.R_OK):
        print(f"Key file is not readable: {key_file}")
        return False
    return True

# Function to create a new key pair
def create_key_pair(key_name):
    try:
        command = [
            "aws", "ec2", "create-key-pair",
            "--key-name", key_name,
            "--query", "KeyMaterial",
            "--output", "text",
            "--region", "us-west-2"
        ]
        key_material = subprocess.check_output(command).decode('utf-8').strip()

        key_file_path = os.path.expanduser(f"~/.ssh/{key_name}.pem")
        with open(key_file_path, 'w') as key_file:
            key_file.write(key_material)

        # Change permissions
        os.chmod(key_file_path, 0o400)
        print(f"Created key pair and saved to {key_file_path}")
        return key_file_path

    except subprocess.CalledProcessError as e:
        print(f"Error creating key pair: {e.output.decode('utf-8')}")
        return None

# Function to find a suitable VPC
def find_default_vpc(region="us-west-2"):
    try:
        command = ["aws", "ec2", "describe-vpcs", "--region", region]
        output = subprocess.check_output(command).decode('utf-8')
        vpcs = json.loads(output)['Vpcs']
        
        # Check for a default VPC
        for vpc in vpcs:
            if vpc.get('IsDefault', False):
                print(f"Found default VPC: {vpc['VpcId']}")
                return vpc['VpcId']
        
        print("No default VPC found.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error finding VPC: {e.output.decode('utf-8')}")
        return None

# Function to create or retrieve a security group in a specific VPC
def create_or_get_security_group(group_name, vpc_id, description="Security group for Pokemon app"):
    try:
        # Check if the security group exists in the specified VPC
        command = ["aws", "ec2", "describe-security-groups", "--filters", f"Name=vpc-id,Values={vpc_id}", f"Name=group-name,Values={group_name}", "--region", "us-west-2"]
        output = subprocess.check_output(command).decode('utf-8')
        security_group_info = json.loads(output)

        if security_group_info['SecurityGroups']:
            security_group_id = security_group_info['SecurityGroups'][0]['GroupId']
            print(f"Security Group {group_name} already exists. ID: {security_group_id}")
            return security_group_id
        else:
            # Create a new security group in the specified VPC
            command = ["aws", "ec2", "create-security-group", "--group-name", group_name, "--description", description, "--vpc-id", vpc_id, "--region", "us-west-2"]
            security_group_output = subprocess.check_output(command).decode('utf-8').strip()
            security_group_id = json.loads(security_group_output)['GroupId']
            print(f"Created new Security Group: {security_group_id}")

            # Add ingress rules
            authorize_ingress(security_group_id)
            return security_group_id
            
    except subprocess.CalledProcessError as e:
        print(f"Error checking security group: {e.output.decode('utf-8')}")
        return None

# Function to authorize ingress for the security group
def authorize_ingress(security_group_id):
    try:
        command = ["aws", "ec2", "authorize-security-group-ingress",
                   "--group-id", security_group_id,
                   "--protocol", "tcp",
                   "--port", "22",
                   "--cidr", "0.0.0.0/0",
                   "--region", "us-west-2"]
        subprocess.check_output(command)
        print("Ingress rules added to Security Group.")
    except subprocess.CalledProcessError as e:
        print(f"Error adding ingress rules: {e.output.decode('utf-8')}")

# Function to run the EC2 instance
def run_ec2_instance(ami_id, security_group_id, key_name):
    try:
        user_data_script = """#!/bin/bash
        sudo yum update -y
        sudo yum install -y git python3 python3-pip
        pip3 install requests boto3
        git clone https://github.com/levi-ochana/pokemon.git /home/ec2-user/pokemon_app
        cd /home/ec2-user/pokemon_app
        pip3 install -r requirements.txt
        echo "Welcome to the Pokémon App! Use this app to draw Pokémon." | sudo tee /etc/motd
        """

        command = [
            "aws", "ec2", "run-instances",
            "--image-id", ami_id,
            "--count", "1",
            "--instance-type", "t2.micro",
            "--key-name", key_name,
            "--security-group-ids", security_group_id,
            "--user-data", user_data_script,
            "--query", "Instances[0].InstanceId",
            "--output", "text",
            "--region", "us-west-2"
        ]
        instance_id = subprocess.check_output(command).decode('utf-8').strip()
        print(f"EC2 Instance launched with ID: {instance_id}")
        return instance_id
    except subprocess.CalledProcessError as e:
        print(f"Error launching instance: {e.output.decode('utf-8')}")

def main():
    key_name = "my-key-pair"
    key_file = os.path.expanduser(f"~/.ssh/{key_name}.pem")

    # Check if the key file exists; if not, create it
    if not os.path.exists(key_file):
        key_file = create_key_pair(key_name)
        if not key_file:
            return  # Stop if key creation failed

    if not check_key_file(key_file):
        return

    ami_id = "ami-0992959aaea5762e8"
    security_group_name = "PokemonAppSG"

    # Find a suitable VPC
    vpc_id = find_default_vpc()

    if vpc_id:
        # Create or get the security group
        security_group_id = create_or_get_security_group(security_group_name, vpc_id)

        if security_group_id:
            # Run the EC2 instance
            run_ec2_instance(ami_id, security_group_id, key_name)

if __name__ == "__main__":
    main()
