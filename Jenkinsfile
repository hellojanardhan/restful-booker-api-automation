pipeline {

    agent any

    stages {

        stage('Parallel Testing') {

            parallel {

                stage('API Tests') {

                    steps {

                        echo 'Executing API tests'

                    }
                }

                stage('UI Tests') {

                    steps {

                        echo 'Executing UI tests'

                    }
                }

                stage('Integration Tests') {

                    steps {

                        echo 'Executing integration tests'

                    }
                }
            }
        }
    }
}
