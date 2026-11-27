pipeline {

    agent any

    stages {

        stage('Welcome') {

            steps {

                echo 'Welcome to Jenkins Pipeline'

            }
        }

        stage('Python Version') {

            steps {

                bat 'python --version'

            }
        }

        stage('Execute Python') {

            steps {

                bat 'python -c "print(\'Hello from Jenkinsfile\')"'

            }
        }
    }
}