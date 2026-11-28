
pipeline {

    agent any

    options {
        timestamps()
    }

    triggers {
        cron('H 2 * * *')
    }

    parameters {
        choice(
            name: 'TEST_SUITE',
            choices: ['create_booking', 'regression', 'update_booking'],
            description: 'Select API test suite'
        )
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out API Automation Framework'
                checkout scm
            }
        }

        stage('Python Setup') {
            steps {
                bat '''
                    if not exist .venv (
                        python -m venv .venv
                    )
                '''
            }
        }

        stage('Install Dependencies') {
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
                        credentialsId: 'booker-api-credentials',
                        usernameVariable: 'BOOKER_USERNAME',
                        passwordVariable: 'BOOKER_PASSWORD'
                    )
                ]) {

                    script {

                        def pytestArgs = ''

                        if (params.TEST_SUITE == 'regression') {
                            pytestArgs = ''
                        }

                        else if (params.TEST_SUITE == 'create_booking') {
                            pytestArgs = '-m create_booking'
                        }

                        else if (params.TEST_SUITE == 'update_booking') {
                            pytestArgs = '-m update_booking'
                        }

                        bat """
                            if not exist reports mkdir reports

                            .venv\\Scripts\\python.exe -m pytest ${pytestArgs} ^
                            --html=reports/report.html ^
                            --self-contained-html ^
                            --junitxml=reports/junit.xml
                        """
                    }
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

            publishHTML(target: [
                reportName: 'API Automation Report',
                reportDir: 'reports',
                reportFiles: 'report.html',
                keepAll: true,
                alwaysLinkToLastBuild: true,
                allowMissing: true
            ])

            archiveArtifacts(
                artifacts: 'reports/**',
                allowEmptyArchive: true
            )

            echo 'API Automation execution completed'
        }

        success {
            echo 'API Automation passed successfully'
        }

        failure {
            echo 'API Automation failed'
        }
    }
}
