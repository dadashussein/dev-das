pipeline {
    agent {
        kubernetes {
            label 'docker-build'
            yaml """
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: jenkins
  containers:
  - name: jenkins-agent
    image: jenkins/inbound-agent:latest
    command:
    - cat
    tty: true
    securityContext:
      privileged: true
  - name: docker
    image: docker:dind
    securityContext:
      privileged: true
  - name: helm
    image: alpine/helm:3.11.1
    command: ['cat']
    tty: true
    volumeMounts:
    - name: aws-config
      mountPath: /root/.aws
  volumes:
  - name: aws-config
    secret:
      secretName: aws-config
"""
        }
    }
    parameters {
        booleanParam(name: 'PUSH_TO_ECR', defaultValue: true, description: 'Push image to ECR and deploy to Kubernetes')
    }
    environment {
        AWS_CREDENTIALS_ID = 'aws_credentials'
        AWS_ACCOUNT_ID = '051826725870'
        ECR_REPOSITORY = '051826725870.dkr.ecr.eu-west-1.amazonaws.com/nestjs'
        IMAGE_TAG = 'latest'
        AWS_REGION = 'eu-west-1'
        GIT_REPO = 'https://github.com/dadashussein/dev-das.git'
        GITHUB_REPO = 'https://github.com/dadashussein/dev-das.git'
        GITHUB_BRANCH = 'main'
    }
    stages {
        stage('Checkout Dockerfile') {
            steps {
                git url: "${GITHUB_REPO}", branch: "${GITHUB_BRANCH}"
            }
        }
        stage('Checkout Application Code') {
            steps {
                git url: "${GIT_REPO}", branch: 'main'
            }
        }
        stage('Prepare Docker') {
            steps {
                container('docker') {
                    sh 'dockerd-entrypoint.sh &>/dev/null &'
                    sh 'sleep 20'
                    sh 'apk add --no-cache aws-cli kubectl'
                    sh 'aws --version'
                    sh 'docker --version'
                    sh 'kubectl version --client'
                }
            }
        }
        stage('Configure AWS') {
            steps {
                container('helm') {
                    withCredentials([aws(credentialsId: "${AWS_CREDENTIALS_ID}")]) {
                        sh '''
                        apk add --no-cache aws-cli
                        aws configure set aws_access_key_id ${AWS_ACCESS_KEY_ID}
                        aws configure set aws_secret_access_key ${AWS_SECRET_ACCESS_KEY}
                        aws configure set region ${AWS_REGION}
                        '''
                    }
                }
            }
        }
        stage('Unit Tests') {
            steps {
                git url: "${GITHUB_REPO}", branch: "${GITHUB_BRANCH}"
                container('docker') {
                    sh 'docker build -t my-app -f Dockerfile .'
                }
            }
        }
        stage('Application Build') {
            steps {
                container('docker') {
                    sh "docker build -t ${ECR_REPOSITORY}:${IMAGE_TAG} ."
                }
            }
        }
        stage('Push Docker Image to ECR') {
            when { expression { params.PUSH_TO_ECR == true } }
            steps {
                script {
                    if (currentBuild.result != 'FAILURE') {
                        env.PUSH_SUCCESSFUL = true
                    } else {
                        env.PUSH_SUCCESSFUL = false
                    }
                    container('docker') {
                        withCredentials([aws(credentialsId: "${AWS_CREDENTIALS_ID}")]) {
                            sh """
                            aws ecr get-login-password --region ${AWS_REGION} | docker login -u AWS --password-stdin ${ECR_REPOSITORY}
                            """
                        }
                        sh "docker push ${ECR_REPOSITORY}:${IMAGE_TAG}"
                    }
                }
            }
        }
        stage('Create ECR Secret') {
            steps {
                container('docker') {
                    withCredentials([aws(credentialsId: "${AWS_CREDENTIALS_ID}")]) {
                        sh """
                        aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPOSITORY}
                        
                        # Create a proper dockerconfigjson secret for ECR
                        DOCKER_AUTH=\$(echo -n "AWS:\$(aws ecr get-login-password --region ${AWS_REGION})" | base64)
                        
                        cat <<EOF | kubectl apply -f -
                        apiVersion: v1
                        kind: Secret
                        metadata:
                          name: ecr-secret
                          namespace: jenkins
                        type: kubernetes.io/dockerconfigjson
                        data:
                          .dockerconfigjson: \$(echo -n '{"auths":{"${ECR_REPOSITORY}":{"auth":"'\${DOCKER_AUTH}'"}}}' | base64 -w 0)
                        EOF
                        """
                    }
                }
            }
        }
        stage('Deploy to Kubernetes with Helm') {
            when { expression { params.PUSH_TO_ECR == true } }
            steps {
                container('helm') {
                    withCredentials([aws(credentialsId: "${AWS_CREDENTIALS_ID}")]) {
                        sh """
                        # Ensure AWS CLI is configured in the Helm container
                        aws configure set aws_access_key_id ${AWS_ACCESS_KEY_ID}
                        aws configure set aws_secret_access_key ${AWS_SECRET_ACCESS_KEY}
                        aws configure set region ${AWS_REGION}
                        
                        # Get ECR token and create Docker config
                        aws ecr get-login-password --region ${AWS_REGION} | helm registry login --username AWS --password-stdin ${ECR_REPOSITORY}
                        
                        helm upgrade --install my-app ./my-app \\
                            --set deployment.myApp.image.repository=${ECR_REPOSITORY} \\
                            --set deployment.myApp.image.tag=${IMAGE_TAG} \\
                            --set imagePullSecrets[0].name=ecr-secret \\
                            --namespace jenkins \\
                            --create-namespace
                        """
                    }
                }
            }
        }
    }
}