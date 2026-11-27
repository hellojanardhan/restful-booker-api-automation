pipeline {
    agent any

    options {
        timestamps()
    }

    parameters {
        choice(
            name: 'TEST_SUITE',
            choices: [
                'functional',
                'negative',
                'security',
                'create_booking',
                'booking_collection',
                'ping',
                'smoke',
                'regression',
                'partial_update',
                'update_booking',
                'delete_booking',
                'e2e'
            ]
        )
    }
    environment {
        BASE_URL = 'http://restful-booker.herokuapp.com'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out API automation framework'
                checkout scm
            }
        }
        stage('Setup Python') {
            steps {
                echo 'Checking Python version'
                bat 'python --version'
                bat '''
                if not exist .venv (
                    python -m venv .venv
                )
                '''
            }
        }

        stage('Install dependencies') {
            steps {
                bat '''
                .venv\\Scripts\\python.exe -m pip install --upgrade pip
                .venv\\Scripts\\python.exe -m pip install -r requirements.txt
                '''
            }
        }
        stage('Execute API Tests') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'booker-api_credentials',
                        usernameVariable: 'BOOKER_USERNAME',
                        passwordVariable: 'BOOKER_PASSWORD'
                    )
                ]) {
                    bat """
                    if not exist reports mkdir reports
                    .venv\\Scripts\\python.exe -m pytest -m "${params.TEST_SUITE}" --html=reports/report.html --self-contained-html --junitxml=reports/junit.xml
                    """
                }
            }
        }
    }
    post {
        always {
            junit(
                testResults: 'reports/junit.xml',
                allowEmptyResults: true
            )

            archiveArtifacts(
                artifacts: 'reports/**',
                allowEmptyArchive: true
            )
            echo 'API Automation execution completed'
        }

        success {
            echo 'API Automation successfully completed'
        }

        failure {
            echo 'API Automation execution failed'
        }
    }
}
