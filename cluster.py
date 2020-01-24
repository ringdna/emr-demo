"""Just a test script that uses boto3 to create an EMR cluster. The same way that airflow will."""
import boto3    

# Variables configured via the infrastructure team.
AWS_REGION='us-east-1'
EMR_BUCKET='ringdna-emr-qa'
EC2_KEYNAME="qa-20191001"
BOOTSTRAP_URI = 's3://{}/scripts/bootstrap.sh'.format(EMR_BUCKET)
EMR_MANAGED_MASTER_SECURITY_GROUP = "sg-e9291c80"
EMR_MANAGED_SLAVE_SECURITY_GROUP = "sg-e9291c80"
SUBNET_ID = "subnet-0734604af9d2cced2"

if __name__ == '__main__':
    client = boto3.client('emr', region_name=AWS_REGION)

    response = client.run_job_flow(
        Name="test_emr", 
        LogUri='s3://{}/logs/'.format(EMR_BUCKET), 
        ReleaseLabel="emr-5.29.0",
        Applications=[
            {
                "Name": "Hadoop"
                # "Version": "2.8.5"
            },
            {
                "Name": "Spark" 
                # "Version": "2.4.4"
            },
            {
                "Name": "Livy"
                # "Version": "0.6.0"
            },
            {
                "Name": "JupyterHub"
                # "Version": "1.0.0"
            }
        ], 
        Instances= { 
            "InstanceGroups": [ 
                { 
                    "Name": "Master nodes", 
                    "Market": "ON_DEMAND", 
                    "InstanceRole": "MASTER",
                    "InstanceType": "m1.xlarge", 
                    "InstanceCount": 1 
                }, 
                { 
                    "Name": "Slave nodes",
                    "Market": "ON_DEMAND",
                    "InstanceRole": "CORE",
                    "InstanceType": "m1.xlarge",
                    "InstanceCount": 2 
                } 
            ],
            "Ec2KeyName": EC2_KEYNAME,
            "KeepJobFlowAliveWhenNoSteps": True, 
            'Ec2SubnetId': SUBNET_ID,
            'EmrManagedMasterSecurityGroup': EMR_MANAGED_MASTER_SECURITY_GROUP, 
            'EmrManagedSlaveSecurityGroup': EMR_MANAGED_SLAVE_SECURITY_GROUP
        },
        Configurations= [
            { 
                "Classification": "jupyter-s3-conf", 
                "Properties": {
                    "s3.persistence.enabled": "true", 
                    "s3.persistence.bucket": EMR_BUCKET
                }
            }
        ],
        VisibleToAllUsers= True, 
        JobFlowRole="EMR_EC2_DefaultRole", 
        ServiceRole="EMR_DefaultRole",

        BootstrapActions= [{
            'Name': 'Install Jupyter Libraries', 
            'ScriptBootstrapAction': { 
                'Path': BOOTSTRAP_URI 
                # 'Args': bootstrap_args,
            }
        }]
    )

    print(response)
