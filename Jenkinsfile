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
    image: alpine/helm:3.11.1  # Helm container
    command: ['cat']
    tty: true
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
        SECRET_NAME = "${AWS_REGION}-ecr-registry"
        DEPLOYMENT_NAME = 'my-app'
        EMAIL = 'huseynzade.dadas@gmail.com'
        GITHUB_REPO = 'https://github.com/dadashussein/dev-das.git'
        GITHUB_BRANCH = 'main'
        NAMESPACE='jenkins'
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
        stage('Unit Tests') {
            steps {
                git url: "${GITHUB_REPO}", branch: "${GITHUB_BRANCH}" // Checkout here as well
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
                    if (currentBuild.result != 'FAILURE') {  //Capture success (or unstable)
                        env.PUSH_SUCCESSFUL = true
                    } else {
                        env.PUSH_SUCCESSFUL = false // Explicitly set to false on failure
                    }
                    container('docker') {
                        withCredentials([aws(credentialsId: "${AWS_CREDENTIALS_ID}")]) {
                            // Log in to ECR
                            sh """
                            aws ecr get-login-password --region ${AWS_REGION} | docker login -u AWS --password-stdin ${ECR_REPOSITORY}
                            """
                        }
                        // Push Docker image to ECR
                        sh "docker push ${ECR_REPOSITORY}:${IMAGE_TAG}"
                    }
                }
            }
        }
        stage('Create ECR Secret') {
            steps {
                container('docker') {
                    withCredentials([aws(credentialsId: "${AWS_CREDENTIALS_ID}")]) {
                        sh '''
                        TOKEN=$(aws ecr --region ${AWS_REGION} get-authorization-token --output text --query authorizationData[].authorizationToken | base64 -d | cut -d: -f2)
                        kubectl delete secret --ignore-not-found ${SECRET_NAME}
                        kubectl create secret docker-registry ${SECRET_NAME} -n ${NAMESPACE} \
                        --docker-server=https://${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com \
                        --docker-username=AWS \
                        --docker-password="${TOKEN}" \
                        --docker-email="${EMAIL}"
                        '''
                    }
                }
            }
        }
        stage('Deploy to Kubernetes with Helm') {
            when { expression { params.PUSH_TO_ECR == true } }
            steps {
                container('helm') {
                    sh """
                    helm upgrade --install my-app ./my-app \\
                        --namespace ${NAMESPACE} \\
                        --create-namespace
                    """
                }
            }
        }
    }
}