import os
import subprocess
import socket


def run_command(command):
    """Run a shell command and handle errors."""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise Exception(f"Command failed with error: {stderr.decode('utf-8')}")
    return stdout.decode('utf-8')


def check_and_install_python():
    """Check if Python is installed, and install it if not."""
    try:
        run_command("python3 --version")  # Check if Python 3 is installed
    except Exception:
        print("Python is not installed. Installing Python...")
        run_command("sudo yum install python3 -y")  # Install Python 3 if not installed


def check_and_install_pip():
    """Check if pip is installed, and install it if not."""
    try:
        run_command("pip3 --version")  # Check if pip is installed
    except Exception:
        print("pip is not installed. Installing pip...")
        run_command("sudo yum install python3-pip -y")  # Install pip if not installed


def setup_aws_cli():
    """Check if AWS CLI is already configured, if not, install and configure it with user credentials."""
    try:
        run_command("aws --version")  # Check if AWS CLI is installed
        config_output = run_command("aws configure list")  # List AWS CLI configuration
        if "None" in config_output:  # Check if any configuration is missing
            print("AWS CLI is not configured. Please provide your credentials.")
            run_command("pip install awscli")  # Install AWS CLI if not installed
            run_command("aws configure")  # Configure AWS CLI with user credentials
        else:
            print("AWS CLI is already configured.")
    except Exception as e:
        print(f"Error checking AWS CLI configuration: {e}")


def create_security_group():
    """Create a security group and add inbound rules for SSH and HTTP."""
    try:
        run_command(
            "aws ec2 create-security-group --group-name my-sg --description 'My security group'")  # Create a new security group
        # Add inbound rules for SSH (port 22) and HTTP (port 80)
        run_command(
            "aws ec2 authorize-security-group-ingress --group-name my-sg --protocol tcp --port 22 --cidr 0.0.0.0/0")
        run_command(
            "aws ec2 authorize-security-group-ingress --group-name my-sg --protocol tcp --port 80 --cidr 0.0.0.0/0")
        print("Security group 'my-sg' created with rules for SSH and HTTP.")
    except Exception as e:
        print(f"Error creating security group: {e}")


def create_key_pair():
    """Create an EC2 key pair for SSH access."""
    try:
        # Create a new key pair and save the private key to MyKeyPair.pem
        run_command("aws ec2 create-key-pair --key-name MyKeyPair --query 'KeyMaterial' --output text > MyKeyPair.pem")
        run_command("chmod 400 MyKeyPair.pem")  # Set permissions on the key file to be readable only by the user
    except Exception as e:
        print(f"Error creating key pair: {e}")


def launch_ec2_instance():
    """Launch an EC2 instance with the specified parameters and return the public IP."""
    try:
        # Launch the EC2 instance using the specified AMI, instance type, key pair, and security group
        output = run_command(
            "aws ec2 run-instances --image-id ami-0c55b159cbfafe1f0 --count 1 --instance-type t2.micro --key-name MyKeyPair --security-groups my-sg --query 'Instances[0].InstanceId' --output text"
        )
        instance_id = output.strip()  # Get the instance ID
        print(f"EC2 instance launched with Instance ID: {instance_id}")

        # Get the public IP address of the launched instance
        ip_output = run_command(
            f"aws ec2 describe-instances --instance-ids {instance_id} --query 'Reservations[0].Instances[0].PublicIpAddress' --output text")
        public_ip = ip_output.strip()

        print(f"Public IP of the instance is: {public_ip}")
        return public_ip
    except Exception as e:
        print(f"Error launching EC2 instance: {e}")


def connect_to_ec2(instance_ip):
    """Connect to the EC2 instance via SSH."""
    try:
        # Check if the key file exists and has the correct permissions
        if not os.path.isfile("MyKeyPair.pem"):
            raise Exception("Key file MyKeyPair.pem does not exist.")

        if not os.access("MyKeyPair.pem", os.R_OK):
            raise Exception("Key file MyKeyPair.pem is not readable.")

        # Ensure correct permissions
        run_command("chmod 400 MyKeyPair.pem")  # Set permissions on the key file

        # Get the local IP address to show which IP is connecting
        local_ip = socket.gethostbyname(socket.gethostname())
        print(f"Connecting to {instance_ip} from local IP {local_ip}...")

        # Connect to the EC2 instance using SSH
        os.system(f"ssh -i 'MyKeyPair.pem' ec2-user@{instance_ip}")
    except Exception as e:
        print(f"Error connecting to EC2 instance: {e}")


def setup_python_on_ec2():
    """Update the system and install Python on the EC2 instance."""
    try:
        run_command("sudo yum update -y")  # Update the system packages
        run_command("sudo yum install python3 -y")  # Install Python 3
        run_command("pip3 install flask")  # Install Flask
    except Exception as e:
        print(f"Error setting up Python on EC2: {e}")


def clone_app_from_github():
    """Clone the application repository from GitHub."""
    try:
        run_command("git clone https://github.com/levi-ochana/pokemon.git")  # Clone the specified GitHub repository
        run_command("cd pokemon")  # Change to the cloned directory
    except Exception as e:
        print(f"Error cloning app from GitHub: {e}")


def run_app():
    """Run the main application script."""
    try:
        run_command("python3 deployment_for_pokemon.py")  # Replace with the actual script name
    except Exception as e:
        print(f"Error running the application: {e}")


def create_startup_script():
    """Create a startup script to run the application on instance boot."""
    try:
        # Create a new shell script to run the application
        with open("start_app.sh", "w") as file:
            file.write("#!/bin/bash\n")  # Indicate this is a bash script
            file.write("cd /home/ec2-user/pokemon\n")  # Change to the application directory
            file.write("python3 deployment_for_pokemon.py\n")  # Run the main application script
        run_command("chmod +x start_app.sh")  # Make the script executable
        # Schedule the script to run at boot time
        run_command("crontab -l | { cat; echo '@reboot /home/ec2-user/start_app.sh'; } | crontab -")
    except Exception as e:
        print(f"Error creating startup script: {e}")


def main():
    """Main function to orchestrate the deployment process."""
    try:
        check_and_install_python()  # Check and install Python
        check_and_install_pip()  # Check and install pip
        setup_aws_cli()  # Check and configure AWS CLI
        create_security_group()  # Create security group
        create_key_pair()  # Create key pair for SSH access
        public_ip = launch_ec2_instance()  # Launch EC2 instance and get its public IP
        connect_to_ec2(public_ip)  # Connect to the EC2 instance
        setup_python_on_ec2()  # Setup Python on the EC2 instance
        clone_app_from_github()  # Clone the application from GitHub
        run_app()  # Run the application
        create_startup_script()  # Create a startup script to run the application on boot
        print("App deployed successfully!")
    except Exception as e:
        print(f"An error occurred in the deployment process: {e}")


if __name__ == "__main__":
    main()  # Run the main function
