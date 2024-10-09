import os
import subprocess
import json
import time

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

        # Change permissions for the key file
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

# Function to get the Public IP of the instance
def get_instance_public_ip(instance_id):
    try:
        command = [
            "aws", "ec2", "describe-instances",
            "--instance-ids", instance_id,
            "--query", "Reservations[0].Instances[0].PublicIpAddress",
            "--output", "text",
            "--region", "us-west-2"
        ]
        public_ip = subprocess.check_output(command).decode('utf-8').strip()
        return public_ip
    except subprocess.CalledProcessError as e:
        print(f"Error getting Public IP: {e.output.decode('utf-8')}")
        return None

# Function to run the EC2 instance and offer SSH connection
def run_ec2_instance(ami_id, security_group_id, key_name):
    try:
        user_data_script = """#!/bin/bash
        sudo yum update -y
        sudo yum install -y git python3 python3-pip
        pip3 install requests boto3
        pip install urllib3==1.26.15
        git clone https://github.com/levi-ochana/pokemon.git /home/ec2-user/pokemon_app
        cd /home/ec2-user/pokemon_app
        pip3 install -r requirements.txt
        pip3 install urllib3==1.26.15
        # מתן הרשאות לכתיבה על ידי ec2-user
        sudo chown -R ec2-user:ec2-user /home/ec2-user/pokemon_app
        sudo chmod -R 755 /home/ec2-user/pokemon_app

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
        
        # Delay to give the instance time to initialize
        time.sleep(10)

        # Get the Public IP of the instance
        public_ip = get_instance_public_ip(instance_id)
        if public_ip:
            print(f"Public IP: {public_ip}")

            # Ask the user if they want to connect via SSH
            connect_ssh = input("Do you want to connect to the instance via SSH? (yes/no): ").strip().lower()
            if connect_ssh == 'yes':
                # Create the SSH command and connect
                ssh_command = f"ssh -i ~/.ssh/{key_name}.pem ec2-user@{public_ip}"
                print(f"Connecting with command: {ssh_command}")
                os.system(ssh_command)  # Execute the SSH command
            else:
                print("You chose not to connect via SSH.")
        else:
            print("Unable to retrieve the Public IP.")
        
        return instance_id
    except subprocess.CalledProcessError as e:
        print(f"Error launching instance: {e.output.decode('utf-8')}")

# Function to delete an existing key pair
def delete_key_pair(key_name):
    try:
        command = [
            "aws", "ec2", "delete-key-pair",
            "--key-name", key_name,
            "--region", "us-west-2"
        ]
        subprocess.check_output(command)
        print(f"Deleted key pair: {key_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error deleting key pair: {e.output.decode('utf-8')}")

# Function to create the key pair if it does not exist or delete and recreate it if it exists
def create_or_replace_key_pair(key_name):
    try:
        # Check if the key pair already exists
        command = [
            "aws", "ec2", "describe-key-pairs",
            "--key-names", key_name,
            "--region", "us-west-2"
        ]
        subprocess.check_output(command)
        print(f"Key pair {key_name} already exists. Recreating...")

        # If the key pair exists, delete it
        delete_key_pair(key_name)

    except subprocess.CalledProcessError:
        print(f"Key pair {key_name} does not exist. Creating a new one...")

    # Create a new key pair after deleting or if it doesn't exist
    return create_key_pair(key_name)

# Main function
def main():
    key_name = "my-key-pair"
    key_file = create_or_replace_key_pair(key_name)  # This will handle both creation and replacement

    if not key_file:
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
