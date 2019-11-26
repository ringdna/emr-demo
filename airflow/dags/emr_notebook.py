import airflow
from airflow.contrib.operators.emr_create_job_flow_operator import EmrCreateJobFlowOperator

# The following variables are set via terraform (infra team).
# The can be stored in s3 and airflow can be configured to read them at run time (in order to setup the EMR cluster).
AWS_REGION='us-west-1'
EMR_BUCKET='emr-airflow'
EC2_KEYNAME="emr-dev"
BOOTSTRAP_URI = 's3://{}/scripts/bootstrap.sh'.format(EMR_BUCKET)
EMR_MANAGED_MASTER_SECURITY_GROUP = "sg-0b7aa2ddd46472f34"
EMR_MANAGED_SLAVE_SECURITY_GROUP = "sg-0b7aa2ddd46472f34"
SUBNET_ID = "subnet-0e0c9ef325662c67d"

args = {
    'owner': 'airflow',
    'start_date': airflow.utils.dates.days_ago(7),
    'provide_context': True
}

dag = airflow.DAG( 
    'test_emr_notebook',
    schedule_interval=None,
    default_args=args,
    max_active_runs=1
)

# https://docs.aws.amazon.com/emr/latest/APIReference/API_RunJobFlow.html
default_emr_settings = { 
    "Name": "test_emr", 
    "LogUri": 's3://{}/logs/'.format(EMR_BUCKET),
    "ReleaseLabel": "emr-5.28.0",
    "Applications": [
        {
            "Name": "Hadoop"
            # "Version": "2.8.5" # Just showing how you can set the versions.
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
    "Instances": { 
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
    "Configurations": [
        { 
            "Classification": "jupyter-s3-conf", 
            "Properties": {
                "s3.persistence.enabled": "true", 
                "s3.persistence.bucket": EMR_BUCKET
            }
        },
        # Spark User Impersonation
        {
            "Classification": "core-site",
            "Properties": {
              "hadoop.proxyuser.livy.groups": "*",
              "hadoop.proxyuser.livy.hosts": "*"
            }
        },
        {
            "Classification": "livy-conf",
            "Properties": {
              "livy.impersonation.enabled": "true"
            }
        }
    ],
    "VisibleToAllUsers": True, 
    "JobFlowRole": "EMR_EC2_DefaultRole", 
    "ServiceRole": "EMR_DefaultRole", 

    "BootstrapActions": [{
        'Name': 'install jupyter libraries', 
        'ScriptBootstrapAction': { 
            'Path': BOOTSTRAP_URI 
            # 'Args': bootstrap_args  # Just showing that we could pass args into the script if we needed.
        }
    }]
}

create_job_flow_task = EmrCreateJobFlowOperator(
    task_id='create_job_flow',
    aws_conn_id='aws_default',
    emr_conn_id='emr_default',
    job_flow_overrides=default_emr_settings,
    dag=dag
)
