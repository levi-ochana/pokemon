import subprocess
import sys
import os
import boto3
import json

# פונקציה להבטיח שהמודול boto3 מותקן
def ensure_boto3_installed():
    try:
        import boto3
    except ImportError:
        print("boto3 לא מותקן. מתקין עכשיו...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "boto3"])
        import boto3  # ניסיון לייבא שוב לאחר ההתקנה

# קריאה לפונקציה
ensure_boto3_installed()

def run_command(command):
    """Run a shell command and return its output."""
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Command failed with error: {result.stderr.strip()}")
        return None
    return result.stdout.strip()

def get_latest_ami():
    """Get the latest Amazon Linux 2 AMI ID."""
    try:
        ami_info = run_command("aws ec2 describe-images --owners amazon --filters 'Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2' --query 'Images[0].ImageId' --output text")
        print(f"Using the latest AMI ID: {ami_info}")
        return ami_info
    except Exception as e:
        print(f"Error fetching latest AMI: {e}")
        return None

def create_security_group():
    """Create a security group if it doesn't already exist."""
    group_name = 'my-sg'
    try:
        # Check if the security group already exists
        existing_group = run_command(f"aws ec2 describe-security-groups --group-names {group_name} --query 'SecurityGroups[0].GroupId' --output text")
        if existing_group:
            print(f"Security group '{group_name}' already exists.")
            return
        run_command(f"aws ec2 create-security-group --group-name {group_name} --description 'My security group'")
        print(f"Security group '{group_name}' created.")
    except Exception as e:
        print(f"Error creating security group: {e}")

def create_key_pair():
    """Create an EC2 key pair."""
    key_name = 'MyKeyPair'
    try:
        run_command(f"aws ec2 create-key-pair --key-name {key_name} --query 'KeyMaterial' --output text > {key_name}.pem")
        print(f"Key pair '{key_name}' created.")
        # Change permissions of the key file
        run_command(f"chmod 400 {key_name}.pem")
    except Exception as e:
        print(f"Error creating key pair: {e}")

def launch_ec2_instance(ami_id):
    """Launch an EC2 instance and return its public IP address."""
    try:
        instance_info = run_command(f"aws ec2 run-instances --image-id {ami_id} --count 1 --instance-type t2.micro --key-name MyKeyPair --security-groups my-sg --query 'Instances[0].InstanceId' --output text")
        print(f"Instance launched: {instance_info}")
        
        # Wait until the instance is running
        print("Waiting for instance to be in running state...")
        run_command(f"aws ec2 wait instance-running --instance-ids {instance_info}")

        # Get public IP address
        public_ip = run_command(f"aws ec2 describe-instances --instance-ids {instance_info} --query 'Reservations[0].Instances[0].PublicIpAddress' --output text")
        return public_ip
    except Exception as e:
        print(f"Error launching EC2 instance: {e}")
        return None

def connect_to_ec2(public_ip):
    """Connect to the EC2 instance using SSH."""
    if public_ip is None:
        print("No public IP available for the instance.")
        return
    try:
        print(f"Connecting to {public_ip} from local IP {os.popen('hostname -I').read().strip()}...")
        run_command(f"ssh -i MyKeyPair.pem ec2-user@{public_ip} 'echo Connected successfully!'")
    except Exception as e:
        print(f"Error connecting to EC2 instance: {e}")

def setup_python_on_ec2(instance_id):
    """Install Python on the EC2 instance."""
    try:
        run_command(f"aws ssm send-command --document-name 'AWS-RunShellScript' --targets 'Key=instanceids,Values={instance_id}' --parameters 'commands=sudo yum install -y python3'")
        print("Python installed on the EC2 instance.")
    except Exception as e:
        print(f"Error setting up Python on EC2: {e}")

def clone_app_from_github():
    """Clone the application repository from GitHub."""
    if os.path.exists("pokemon"):
        print("The directory 'pokemon' already exists. Skipping clone.")
        return
    try:
        run_command("git clone https://github.com/levi-ochana/pokemon.git")  # Clone the specified GitHub repository
        print("Application cloned from GitHub.")
    except Exception as e:
        print(f"Error cloning app from GitHub: {e}")

def run_app():
    """Run the application on the EC2 instance."""
    try:
        run_command("aws ssm send-command --document-name 'AWS-RunShellScript' --targets 'Key=instanceids,Values=<Your_Instance_ID>' --parameters 'commands=cd pokemon && python3 app.py'")
        print("Application running on the EC2 instance.")
    except Exception as e:
        print(f"Error running the application: {e}")

def create_startup_script():
    """Create a startup script to run the application on boot."""
    startup_script = """#!/bin/bash
    cd /path/to/pokemon  # עדכן את הנתיב בהתאם למיקום התיקיה של האפליקציה שלך
    python3 app.py &
    """
    with open("startup.sh", "w") as f:
        f.write(startup_script)
    run_command("chmod +x startup.sh")
    print("Startup script created.")

def main():
    """Main function to orchestrate the deployment process."""
    try:
        ami_id = get_latest_ami()  # Get the latest AMI ID
        if not ami_id:
            print("No valid AMI ID found. Exiting...")
            return
        
        create_security_group()  # Create security group
        create_key_pair()  # Create key pair for SSH access
        public_ip = launch_ec2_instance(ami_id)  # Launch EC2 instance and get its public IP
        
        if public_ip is None:
            print("No public IP available for the instance.")
            return
        
        connect_to_ec2(public_ip)  # Connect to the EC2 instance
        instance_id = run_command(f"aws ec2 describe-instances --filters 'Name=ip-address,Values={public_ip}' --query 'Reservations[0].Instances[0].InstanceId' --output text")
        setup_python_on_ec2(instance_id)  # Setup Python on the EC2 instance
        clone_app_from_github()  # Clone the application from GitHub
        run_app()  # Run the application
        create_startup_script()  # Create a startup script to run the application on boot
        print("App deployed successfully!")
    except Exception as e:
        print(f"An error occurred in the deployment process: {e}")

if __name__ == "__main__":
    main()  # Run the main function
