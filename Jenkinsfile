pipeline {
    agent any

    environment {
        VENV = 'venv'
        DJANGO_SETTINGS_MODULE = 'Website.settings'
        PYTHONPATH = '.'
    }

    options {
        timeout(time: 40, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                sh '''
                    if ! python3 -m venv --help > /dev/null 2>&1; then
                        echo "ERROR: python3-venv is not installed. Please install it on the Jenkins agent using:"
                        echo "sudo apt-get update && sudo apt-get install python3-venv"
                        exit 1
                    fi
                '''
                sh 'python3 -m venv $VENV'
                sh '. $VENV/bin/activate && pip install --upgrade pip'
                sh '. $VENV/bin/activate && pip install -r requirements.txt'
                sh '. $VENV/bin/activate && pip install flake8 coverage pytest pytest-django pytest-cov safety bandit'
            }
        }

        stage('Static Analysis') {
            steps {
                sh '. $VENV/bin/activate && flake8 . --count --show-source --statistics'
                sh '. $VENV/bin/activate && bandit -r . || true'
            }
        }

        stage('Security Check') {
            steps {
                sh '. $VENV/bin/activate && safety check || true'
            }
        }

        stage('Unit Tests & Coverage') {
            steps {
                sh '. $VENV/bin/activate && coverage run --source=. manage.py test'
                sh '. $VENV/bin/activate && coverage xml'
                sh '. $VENV/bin/activate && coverage html'
            }
        }

        stage('Pytest Advanced') {
            steps {
                sh '. $VENV/bin/activate && pytest --ds=Website.settings --junitxml=pytest-report.xml --cov=. --cov-report=xml'
            }
        }

        stage('Collect Static') {
            steps {
                sh '. $VENV/bin/activate && python manage.py collectstatic --noinput'
            }
        }

        stage('Publish Artifacts') {
            steps {
                archiveArtifacts artifacts: 'coverage.xml, pytest-report.xml, htmlcov/**, static/**', allowEmptyArchive: true
            }
        }
    }

    post {
        success {
            junit 'pytest-report.xml'
            publishHTML(target: [
                reportDir: 'htmlcov',
                reportFiles: 'index.html',
                reportName: 'Coverage Report',
                keepAll: true,
                alwaysLinkToLastBuild: true,
                allowMissing: true
            ])
        }
        always {
            cleanWs()
        }
    }
}
