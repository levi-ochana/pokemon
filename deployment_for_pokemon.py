import os
import subprocess
import json
import time

# Function to execute AWS CLI command and return output
def run_aws_command(command):
    try:
        return subprocess.check_output(command).decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.output.decode('utf-8')}")
        return None

# Key pair management - create or replace if exists
def manage_key_pair(key_name):
    key_file_path = os.path.expanduser(f"~/.ssh/{key_name}.pem")
    
    # Check if the key file exists and change permissions to 600 if it does
    if os.path.exists(key_file_path):
        os.chmod(key_file_path, 0o600)
        print(f"Changed permissions to 600 for existing key file: {key_file_path}")
    
    # Check if key pair exists in AWS and delete if necessary
    key_pair_exists = run_aws_command([
        "aws", "ec2", "describe-key-pairs", "--key-names", key_name, "--region", "us-west-2"
    ])

    if key_pair_exists:
        print(f"Key pair {key_name} exists, recreating...")
        run_aws_command(["aws", "ec2", "delete-key-pair", "--key-name", key_name, "--region", "us-west-2"])

    # Create a new key pair
    key_material = run_aws_command([
        "aws", "ec2", "create-key-pair", "--key-name", key_name, "--query", "KeyMaterial", "--output", "text", "--region", "us-west-2"
    ])
    
    if key_material:
        with open(key_file_path, 'w') as key_file:
            key_file.write(key_material)
        
        # Change permissions to 600 after creating the new key pair
        os.chmod(key_file_path, 0o600)
        print(f"Key pair created and saved to {key_file_path}. Permissions set to 600.")
        
        return key_file_path
    return None

# Function to find a suitable VPC
def find_default_vpc(region="us-west-2"):
    vpcs = run_aws_command(["aws", "ec2", "describe-vpcs", "--region", region])
    if vpcs:
        vpcs = json.loads(vpcs)['Vpcs']
        for vpc in vpcs:
            if vpc.get('IsDefault', False):
                print(f"Found default VPC: {vpc['VpcId']}")
                return vpc['VpcId']
    print("No default VPC found.")
    return None

# Security group creation or retrieval
def create_security_group(group_name, vpc_id, description="Security group for Pokemon app"):
    security_group_info = run_aws_command([
        "aws", "ec2", "describe-security-groups", "--filters",
        f"Name=vpc-id,Values={vpc_id}", f"Name=group-name,Values={group_name}", "--region", "us-west-2"
    ])
    
    if security_group_info and json.loads(security_group_info)['SecurityGroups']:
        security_group_id = json.loads(security_group_info)['SecurityGroups'][0]['GroupId']
        print(f"Security Group {group_name} already exists. ID: {security_group_id}")
        return security_group_id
    
    security_group_id = run_aws_command([
        "aws", "ec2", "create-security-group", "--group-name", group_name,
        "--description", description, "--vpc-id", vpc_id, "--region", "us-west-2"
    ])
    
    if security_group_id:
        print(f"Security Group created: {security_group_id}")
        run_aws_command([
            "aws", "ec2", "authorize-security-group-ingress", "--group-id", security_group_id,
            "--protocol", "tcp", "--port", "22", "--cidr", "0.0.0.0/0", "--region", "us-west-2"
        ])
        print("Ingress rules added to Security Group.")
    return security_group_id

# Function to get the Public IP of the instance
def get_instance_public_ip(instance_id):
    public_ip = run_aws_command([
        "aws", "ec2", "describe-instances",
        "--instance-ids", instance_id,
        "--query", "Reservations[0].Instances[0].PublicIpAddress",
        "--output", "text",
        "--region", "us-west-2"
    ])
    return public_ip

# Function to run the EC2 instance and offer SSH connection
def run_ec2_instance(ami_id, security_group_id, key_name):
    user_data_script = """#!/bin/bash
    sudo yum update -y
    sudo yum install -y git python3 python3-pip
    pip3 install requests boto3
    git clone https://github.com/levi-ochana/pokemon.git /home/ec2-user/pokemon_app
    cd /home/ec2-user/pokemon_app
    pip3 install -r requirements.txt
    pip3 install urllib3==1.26.15
    sudo chown -R ec2-user:ec2-user /home/ec2-user/pokemon_app
    sudo chmod -R 755 /home/ec2-user/pokemon_app

    echo "Welcome to the Pokémon App! Use this app to draw Pokémon." | sudo tee /etc/motd
    """

    instance_id = run_aws_command([
        "aws", "ec2", "run-instances",
        "--image-id", ami_id, "--count", "1", "--instance-type", "t2.micro",
        "--key-name", key_name, "--security-group-ids", security_group_id,
        "--user-data", user_data_script, "--query", "Instances[0].InstanceId",
        "--output", "text", "--region", "us-west-2"
    ])
    
    if instance_id:
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
    return None

# Main function
def main():
    key_name = "my-key-pair"
    key_file = manage_key_pair(key_name)  # This will handle both creation and replacement

    if not key_file:
        return

    ami_id = "ami-0992959aaea5762e8"
    security_group_name = "PokemonAppSG"

    # Find a suitable VPC
    vpc_id = find_default_vpc()

    if vpc_id:
        # Create or get the security group
        security_group_id = create_security_group(security_group_name, vpc_id)

        if security_group_id:
            # Run the EC2 instance
            run_ec2_instance(ami_id, security_group_id, key_name)

if __name__ == "__main__":
    main()
