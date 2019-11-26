# Example JupyterHub Notebook integration with AWS EMR and Airflow

This repo uses:
- the [turbine airflow stack](https://github.com/villasv/aws-airflow-stack) in order to provision airflow.
- terraform in order to provision the EMR resources (public VPC, s3 buckets, etc) that an airflow dag will use to create an EMR cluster.

The workflow for creating an EMR cluster via airflow and accessing jupyter follows:

- The notebook dag defined in `./airflow/dags/emr_notebook.py` can be triggered by a user(data scientist) that wants a secure/beefy EMR cluster in order to run some jupyter notebook code against.
- The user(data scientist) could be responsible for deleting the cluster when finished with it.

The idea is that the infrastructure team can focus on the security(security groups/ssh/etc) required to run an EMR cluster and access sensitive data.
And that airflow(data scientist user) handles the EMR Cluster lifecycles (scheduled/triggered), given the infrastructure configuration.

# AWS Managed Notebooks

AWS has made it pretty easy to run shared notebooks backed by an EMR cluster. 
[AWS Notebooks](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-managed-notebooks.html) offer a serverless/managed jupyterhub platform.

## [Python Dependencies](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-managed-notebooks-considerations.html)

EMR Notebooks runs Jupyter Notebook version 5.7.0 and Python 3.6.5.
EMR Notebooks is pre-configured with the following kernels and library packages installed:
- Kernels
- PySpark
- PySpark3
- Python3
- Spark
- SparkR


If you require additional libraries that all users can access, you can install them using bootstrap actions. You can install additional library packages from within the notebook editor. These libraries are notebook-scoped libraries. They are available only to the current notebook session. They do not interfere with cluster-wide libraries or libraries installed within other notebooks.

## [Security Groups](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-managed-notebooks-security-groups.html)

When you create an EMR notebook, two security groups are used to control network traffic between the EMR notebook and the Amazon EMR cluster when the notebook editor is used. The default security groups have minimal rules that allow only network traffic between the EMR Notebooks service and the clusters to which notebooks are attached.

I believe that as long as you [lock down the EMR Cluster](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-security-groups.html), only allowing it access to redshift/s3/etc, the default notebook security group should be "production ready".

## [Working with EMR Notebooks](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-managed-notebooks-working-with.html)

An advantage of using an EMR notebook is that you can launch the notebook in Jupyter or JupyterLab directly from the console.

With EMR Notebooks, the notebook editor you access from the Amazon EMR console is the familiar open-source Jupyter Notebook editor or JupyterLab. Because the notebook editor is launched within the Amazon EMR console, it's more efficient to configure access than it is with a notebook hosted on an Amazon EMR cluster. You don't need to configure a user's client to have web access through SSH, security group rules, and proxy configurations. If a user has sufficient permissions, they can simply open the notebook editor within the Amazon EMR console.

## Issues

The main problem I've encountered with this simple set up is the fact that the [CloudFormation template doesn't make it easy to configure an EC2 Instance Profile for the airflow workers](https://github.com/villasv/aws-airflow-stack/issues/69).
These worker nodes need access to AWS EMR in order to create clusters.
Ive simply added the following policy manually to the airflow role(arn:aws:iam::${my-account}:role/airflow-ring-TurbineCluster-${uuid}-AirflowRole-${uuid}) produced from the CloudFormation stack:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": "elasticmapreduce:*",
            "Resource": "*"
        }
    ]
}
```


